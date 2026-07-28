# ADR-008: Open data sources instead of ProCyclingStats scraping

## Status

Accepted — supersedes [ADR-003](003-pcs-data-source.md)

## Context

[ADR-003](003-pcs-data-source.md) selected ProCyclingStats (PCS) as the primary data source, assuming a rate-limited, `robots.txt`-respecting HTTP client would be sufficient and appropriate.

That assumption no longer holds. PCS now sits behind Cloudflare bot protection and serves an interactive challenge page to automated clients.

Verified during investigation (2026-07-28):

| Source | Result |
|--------|--------|
| `procyclingstats.com/race/tour-de-france/2023/startlist` | **403** — Cloudflare "Just a moment..." challenge, with both a project User-Agent and a Chrome User-Agent |
| `firstcycling.com` | **403** |
| Wikipedia REST API | **200** |
| Wikidata SPARQL endpoint | **200** |
| Open-Meteo archive API | **200** |

This changes the nature of the decision. Honouring `robots.txt` and throttling requests is respectful scraping. Defeating an interactive bot challenge requires TLS-fingerprint impersonation (`curl_cffi`) or a headless browser (Playwright), which means deliberately circumventing a control the site operator has explicitly put in place. That carries terms-of-service exposure, ongoing fragility as Cloudflare rules change, an inability to run in CI, and a poor signal to anyone reviewing this repository.

## Decision

Adopt a **hybrid source strategy**, with legitimacy as the primary constraint.

**Primary source: Wikipedia REST API**, supplemented by Wikidata for entity resolution where useful.

- Public, documented API intended for programmatic access
- Content licensed CC BY-SA, so attribution is sufficient for this project's use
- Coverage verified for Tour de France editions 2015–2024
- Per edition, three pages carry the data we need: the edition overview, `Stage 1 to Stage 11`, and `Stage 12 to Stage 21`

Structure verified against the 2023 edition:

| Data | Location | Shape |
|------|----------|-------|
| Stage schedule | Overview, `Route and stages` table | `Stage \| Date \| Course \| Distance \| Elevation gain \| Type \| Winner` |
| Stage result (top 10) | Stage-range page | `Rank \| Rider \| Team \| Time`, `<caption>Stage N Result</caption>` |
| GC after each stage | Stage-range page | same shape, `<caption>General classification after Stage N</caption>` |
| Final GC (full field) | Overview, top-10 table plus collapsed continuation | 150 riders for 2023 |
| Jersey holders per stage | Overview, `Classification leadership` table | one row per stage |
| Points / mountains / young / team classifications | Overview | `Rank \| Rider \| Team \| Points\|Time` |

Two properties make parsing tractable: tables are `wikitable plainrowheaders` with a stable
`Rank | Rider | Team | Time` header, and the `<caption>` text distinguishes a stage result
from a GC standing, so parsers do not depend on document order. Rider and team cells carry
wikilinks (`./Adam_Yates`), which give stable slugs for identity mapping.

**Weather source: Open-Meteo archive API** — unchanged from the original M2-05 plan.

**PCS adapter: retained but opt-in only.** The `PCSClient` built in #16 stays in the codebase as a `CyclingDataSource` implementation. It is never enabled in CI or in Docker defaults, and using it is the operator's decision and responsibility.

A curated bulk dataset (Kaggle/GitHub) was considered as an additional primary source. It is **deferred**: Wikipedia already covers stages, results, GC standings, teams and riders, and adding a third-party dataset whose licence and coverage we would have to underwrite is an unnecessary dependency. It remains available as a future adapter if a concrete gap appears.

## Consequences

**Easier**

- Fully legitimate data access, safe to run in CI and to show in a portfolio
- A real API instead of HTML scraping, so parsing is far more stable
- The existing `RateLimiter` and `FileResponseCache` from #16 are reused directly — Wikipedia returns **429** on burst requests, so throttling remains necessary
- Zero churn in the domain and application layers, because ingestion sits behind the `CyclingDataSource` port

**Harder**

- **Reduced per-stage granularity.** Individual stage results are top-10 only, so we cannot answer "who finished 87th on stage 12". Note that the *final* general classification is available for the full field (150 riders in 2023), and GC standings are available after every stage, so overall placings are not limited to the top 10.
- Attribution required under CC BY-SA
- Article structure is stable but editorially maintained, so parsers need defensive handling and validation (M2-07)

**Impact on the ML plan**

The granularity limit was reviewed against the milestone goals and accepted. Stage-winner, GC, podium and top-10 models are all still trainable, and full final GC plus per-stage GC standings support fatigue and form features better than a top-10-only source would. What is lost is mid-pack *stage* signal, which no milestone depends on. If models later plateau in a way traceable to this gap, revisit with a new ADR.

## Alternatives considered

- **Cloudflare evasion via `curl_cffi` or Playwright** — rejected. Richest available data, but requires circumventing an explicit anti-bot control, breaks unpredictably, cannot run in CI, and bloats the Docker image.
- **Curated bulk dataset as primary** — deferred, as described above. No live/current-season data and unverified licensing.
- **Commercial data providers** — still cost-prohibitive for a portfolio project.
- **Synthetic fixtures only** — rejected as a primary strategy; real data is central to the project's purpose. Fixtures are still used for unit tests.
