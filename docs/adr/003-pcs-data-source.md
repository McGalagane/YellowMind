# ADR-003: ProCyclingStats as primary data source

## Status

Superseded by [ADR-008](008-open-data-sources.md)

PCS moved behind Cloudflare bot protection and now returns HTTP 403 with an interactive
challenge for automated clients. Reaching the content would require circumventing that
control, so Wikipedia became the primary source instead. The `PCSClient` adapter is
retained as opt-in, local-only.

## Context

YellowMind requires comprehensive historical Tour de France data: riders, teams, stages, results, and profiles. Official ASO data is not freely available in machine-readable form.

## Decision

Use **ProCyclingStats (PCS)** as the primary data source for historical ingestion, accessed via a rate-limited HTTP client with local caching to Parquet.

## Consequences

- **Easier:** Rich historical coverage back to 2015+; well-understood HTML structure
- **Harder:** Scraping fragility if PCS changes layout; must respect rate limits and terms of use; no commercial redistribution of raw data

## Alternatives considered

- **Manual CSV curation** — rejected; not scalable, poor portfolio signal
- **Commercial data providers** — deferred; cost prohibitive for portfolio project
