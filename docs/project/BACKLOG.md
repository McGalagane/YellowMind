# YellowMind — Project Backlog (M2–M10)

Future milestones and issues for the YellowMind platform: Tour de France stage winner, GC, podium, and top-10 predictions with Monte Carlo simulation.

**Status:** Planned — not yet tracked on GitHub.

**Prerequisites:** Milestone 1 (Project Foundation) must be complete before starting M2.

---

## Milestone 2 — Historical Data Ingestion

Support ingestion of riders, teams, stages, results, weather, and stage profiles from the Wikipedia REST API, per [ADR-008](../adr/008-open-data-sources.md).

> **Source change:** ProCyclingStats moved behind Cloudflare bot protection and is no longer a viable primary source. Wikipedia is now primary; the `PCSClient` adapter is retained as opt-in, local-only. Consequence: individual **stage** results are top-10 only, though the full final GC and per-stage GC standings are available.

### Issue M2-01: HTTP client and rate-limited transport — **done (#16)**

| Field | Detail |
|-------|--------|
| **Objective** | Reliable, respectful access to an external cycling data provider. |
| **Description** | HTTP client with retries, exponential backoff, response caching, and configurable User-Agent. Abstract `CyclingDataSource` port in application layer. |
| **Acceptance criteria** | Fetches a known page without error; rate limit configurable via env; unit tests with mocked HTTP responses. |
| **Technical notes** | Shipped as `PCSClient`. The `RateLimiter` and `FileResponseCache` are provider-agnostic and reused by the Wikipedia adapter, which also returns 429 on burst requests. Never commit fetched HTML to git. |
| **Dependencies** | Milestone 1 complete |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-02a: Startlist parser — riders and teams

| Field | Detail |
|-------|--------|
| **Objective** | Turn the startlist article into structured rider and team records. |
| **Description** | Parse the article `List of teams and cyclists in the {year} Tour de France`, which holds the complete field in one flat table: bib number, rider name and slug, nationality, team name and slug, age, final GC position, and abandonment. |
| **Acceptance criteria** | All editions 2015-2024 parse with rider counts matching the source; finishers plus abandonments equal the field size; tables located by header signature rather than document position. |
| **Technical notes** | **Corrected:** riders are *not* on the edition overview page — its teams section lists only the 22 team names. Team wikilinks resolve to the article's current title while the cell text is the historical name, so both are retained: the slug is the stable cross-edition key, the text is what the team was called that year. `Pos.` encodes abandonment as `DNF-14`, `DNS-18`, `HD`, `OTL`, `COV`, or `DSQ`, optionally suffixed with the stage. |
| **Dependencies** | M2-01 |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-02b: Rider identity and participation model — **done (#25)**

| Field | Detail |
|-------|--------|
| **Objective** | Align the entity model with the data the source actually provides. |
| **Description** | The M1 entities assumed PCS fields. `Rider` was bound to a team, and teams to an edition, so rider identity could not survive across editions; `birth_date` and team nationality were required but are never published. Splits `Rider` (identity) from the new `RiderParticipation` (per-edition team, bib, age, GC position, abandonment). |
| **Acceptance criteria** | Rider identity is edition-independent; abandonment has a home; migration verified up and down against PostgreSQL. |
| **Technical notes** | See [ADR-009](../adr/009-rider-identity-and-participation.md). `AbandonmentKind` moved into the domain; the source-token mapping stays in the adapter. Nationality stores the source's country name, so columns widened from `String(3)`. |
| **Dependencies** | M2-02a |
| **Labels** | `milestone-2`, `area:data`, `complexity:L` |

### Issue M2-02c: Tour edition ingestion — **done (#27)**

| Field | Detail |
|-------|--------|
| **Objective** | Persist the `TourEdition` aggregate root so everything else has an anchor. |
| **Description** | Teams, participations, and stages all carry a `tour_edition_id`, and the edition's dates are non-nullable, so nothing could be stored until this existed. No `TourEditionRepository` implementation existed either. Dates come from the overview article's infobox, which is independent of the `Route and stages` table, so this does not duplicate M2-03. |
| **Acceptance criteria** | Parser verified against all editions 2015-2024; re-running the ingestion changes nothing; end-to-end test from HTML to a reloaded entity. |
| **Technical notes** | The `Dates` row varies: `4–26 July 2015` omits the start month, 2020 uses an **em** dash with a footnote marker and crosses months, 2021 and 2024 cross months with an en dash. Month names are mapped explicitly, since `strptime("%B")` is locale-dependent. The year is taken from the article rather than the caller, so a misfetched page fails instead of being stored against the wrong edition. `EditionRecord` is a source-agnostic use-case input in the application layer, keeping HTML out of the use case. |
| **Dependencies** | M2-02b |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-02d: Persist riders and teams — **done (#29)**

| Field | Detail |
|-------|--------|
| **Objective** | Store parsed riders, teams, and participations in PostgreSQL. |
| **Description** | Map startlist records onto the domain entities, assign internal UUIDs keyed on source slugs, and persist idempotently. |
| **Acceptance criteria** | Ingests riders, teams, and participations; re-running changes nothing. Verified across 2015-2024 against PostgreSQL: 10 editions, 221 teams, **642 riders, 1,834 participations**, with a second pass creating nothing. |
| **Technical notes** | Deduplicate riders across editions on `rider_slug`, and teams on `(edition, team_slug)`, since sponsor changes rename teams between years. Handle mid-Tour transfers as an edge case (document in an ADR if deferred). The Parquet mirror is deliberately excluded: the analytical store applies to every ingestion type, so it is established once in its own issue rather than bolted onto each. |
| **Dependencies** | M2-02c, since participations need an edition to attach to |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-03: Stage ingestion — **done (#31)**

| Field | Detail |
|-------|--------|
| **Objective** | Ingest all 21 stages per edition: number, date, terrain type, distance. |
| **Description** | Parse the overview `Route and stages` table. Verified across 2015-2024: exactly 210 stages, idempotent on a second pass. |
| **Acceptance criteria** | 21 stages per edition for all ten; terrain mapped for every spelling; rest-day and total rows skipped; unique on `(edition, number)`. |
| **Technical notes** | Two traps found by surveying all ten editions. The `Type` header carries `colspan=2` (a pictogram cell plus a label cell) in **every** edition, so a naive header-to-column mapping reads the icon as the terrain and the terrain as the winner, silently — hence `data_columns`, `header_span`, and `span_text`. 2018 renames the header to `Stage type`. Terrain has 10 spellings across 210 stages: `Hilly stage` and `Medium mountain stage` are the same category renamed over the decade, and `Mountain time trial` justified adding `MOUNTAIN_TT` to `StageType`, since it rewards climbers rather than time-trial specialists. |
| **Dependencies** | M2-02c |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

> **Correction:** the original description assumed the route table carried `elevation gain`, which came from looking only at 2023. It is present **only** in 2023 — 21 of 210 stages. `StageProfile` is therefore not ingested here: its `finish_type` and `profile_score` appear nowhere in the source (they are derived features), and `elevation_gain_m` is non-nullable but available for one edition in ten. It belongs to feature engineering in M3, and elevation needs its own source. Tracked separately rather than half-filled.

### Issue M2-04: Race results ingestion

| Field | Detail |
|-------|--------|
| **Objective** | Ingest per-stage results and GC standings. |
| **Description** | Rank, time, time gap, and status for the top-10 finishers per stage, plus the GC standings table that follows each stage. |
| **Acceptance criteria** | Results for TDF 2023 stage 1 and its GC table; parser tolerates missing/annotated cells; GC standing queryable per stage. |
| **Technical notes** | Link results to `Rider`, `Stage`, `TourEdition`. Store raw + normalized in bronze/silver Parquet. |
| **Dependencies** | M2-02, M2-03 |
| **Labels** | `milestone-2`, `area:data`, `complexity:L` |

### Issue M2-05: Weather data ingestion

| Field | Detail |
|-------|--------|
| **Objective** | Attach historical weather conditions to each stage. |
| **Description** | Integrate Open-Meteo archive API (or equivalent) using stage date and approximate location. Temperature, wind, precipitation. |
| **Acceptance criteria** | Weather record linked to every stage in TDF 2023; missing geo data logged, not silently skipped. |
| **Technical notes** | Stage start/finish coordinates from profile or manual seed for MVP. |
| **Dependencies** | M2-03 |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-06: Prefect orchestration for ingestion flows

| Field | Detail |
|-------|--------|
| **Objective** | Scheduled, observable, retriable ingestion pipelines. |
| **Description** | Prefect flow chaining M2-02 through M2-05. Bronze → silver → PostgreSQL promotion. |
| **Acceptance criteria** | Single command ingests full TDF 2023; failures logged in Prefect UI; partial runs resumable. |
| **Technical notes** | Flow parameters: `edition_year`, `stages` (optional subset). |
| **Dependencies** | M2-02, M2-03, M2-04, M2-05, M1 Docker Compose |
| **Labels** | `milestone-2`, `area:data`, `complexity:L` |

### Issue M2-07: Data validation and quality checks

| Field | Detail |
|-------|--------|
| **Objective** | Catch bad or incomplete ingested data before downstream use. |
| **Description** | Validation suite: row counts, referential integrity, no duplicate results, stage completeness (21 stages). |
| **Acceptance criteria** | Validation runs as final step of ingestion flow; failures block silver promotion; report written to logs. |
| **Technical notes** | Consider Great Expectations or lightweight custom validators. |
| **Dependencies** | M2-06 |
| **Labels** | `milestone-2`, `area:data`, `complexity:M` |

### Issue M2-08: Backfill historical Tours (2015–2024)

| Field | Detail |
|-------|--------|
| **Objective** | Build a 10-edition training corpus. |
| **Description** | Run ingestion flow for TDF 2015–2024 with monitoring and failure recovery. |
| **Acceptance criteria** | All 10 editions pass validation; documented row counts per edition; ingestion duration logged. |
| **Technical notes** | Long-running batch — run via Prefect deployment, not CI. |
| **Dependencies** | M2-06, M2-07 |
| **Labels** | `milestone-2`, `area:data`, `complexity:L` |

---

## Milestone 3 — Feature Engineering

Build feature generators for rider, team, race context, fatigue, weather, and stage profile signals.

### Issue M3-01: Feature store schema and DuckDB setup

| Field | Detail |
|-------|--------|
| **Objective** | Analytical storage for training and inference feature matrices. |
| **Description** | DuckDB database schema, Parquet layout conventions (`data/features/{edition}/{stage}.parquet`), read/write adapters. |
| **Acceptance criteria** | Feature matrix readable by pandas and Polars; schema versioned in docs; integration test round-trip. |
| **Dependencies** | Milestone 2 complete |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-02: Rider feature generator

| Field | Detail |
|-------|--------|
| **Objective** | Rider-level features for prediction models. |
| **Description** | Age, career stage wins, GC top-10 history, specialty tags, days since last win. Point-in-time: no future leakage. |
| **Acceptance criteria** | Features computed for all starters in TDF 2023 stage 10; unit tests verify no lookahead bias. |
| **Dependencies** | M3-01 |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-03: Team feature generator

| Field | Detail |
|-------|--------|
| **Objective** | Team-level strength and role features. |
| **Description** | Team win rate, designated GC leader flag, climbing/sprint depth scores. |
| **Acceptance criteria** | One row per rider-team-stage with team features joined. |
| **Dependencies** | M3-01 |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-04: Race context features

| Field | Detail |
|-------|--------|
| **Objective** | Situational features within the Tour. |
| **Description** | Stage number, rest days before stage, cumulative distance, GC gap to leader at stage start, jersey holders. |
| **Acceptance criteria** | GC standings correctly reconstructed at each stage boundary; tested against known 2023 standings. |
| **Dependencies** | M3-01 |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-05: Fatigue features

| Field | Detail |
|-------|--------|
| **Objective** | Model accumulated workload and recovery. |
| **Description** | Consecutive racing days, elevation load last 3 stages, workload score, rest day indicator. |
| **Acceptance criteria** | Fatigue monotonically increases over consecutive stages; resets after rest days. |
| **Dependencies** | M3-01 |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-06: Weather features

| Field | Detail |
|-------|--------|
| **Objective** | Encode weather impact on stage outcomes. |
| **Description** | Temperature bins, wind speed/direction categories, rain binary, heat stress index. |
| **Acceptance criteria** | All stages with weather data have encoded features; null strategy documented. |
| **Dependencies** | M3-01, M2-05 |
| **Labels** | `milestone-3`, `area:features`, `complexity:S` |

### Issue M3-07: Stage profile features

| Field | Detail |
|-------|--------|
| **Objective** | Encode stage difficulty and type. |
| **Description** | Distance, elevation gain, profile score, climb count, finish type (flat/uphill/downhill), TT length. |
| **Acceptance criteria** | TT stages flagged distinctly; mountain stages have elevated climb features. |
| **Dependencies** | M3-01 |
| **Labels** | `milestone-3`, `area:features`, `complexity:M` |

### Issue M3-08: Feature pipeline orchestration

| Field | Detail |
|-------|--------|
| **Objective** | End-to-end feature generation via Prefect. |
| **Description** | Flow combining M3-02–M3-07 into unified feature matrix per stage-edition. |
| **Acceptance criteria** | Full feature matrix for TDF 2023; reproducible with pinned dependencies; runtime logged. |
| **Dependencies** | M3-02 through M3-07 |
| **Labels** | `milestone-3`, `area:features`, `complexity:L` |

### Issue M3-09: Feature documentation and lineage

| Field | Detail |
|-------|--------|
| **Objective** | Document every feature for reproducibility and portfolio clarity. |
| **Description** | Feature catalog markdown: name, type, source, computation, leakage risk. |
| **Acceptance criteria** | Catalog covers all M3 features; linked from README. |
| **Dependencies** | M3-08 |
| **Labels** | `milestone-3`, `area:docs`, `complexity:S` |

---

## Milestone 4 — Rating Engine

Multi-dimensional rider ratings consumed as features by prediction models.

### Issue M4-01: Rating domain model and interfaces

| Field | Detail |
|-------|--------|
| **Objective** | Define rating entities and update contracts. |
| **Description** | `RiderRating` value object, `RatingEngine` port, rating history storage interface. |
| **Acceptance criteria** | Domain tests for rating bounds (e.g. 1000–3000 Elo scale); no infrastructure in domain. |
| **Dependencies** | Milestone 3 complete |
| **Labels** | `milestone-4`, `area:model`, `complexity:S` |

### Issue M4-02: Climbing rating (Elo-style)

| Field | Detail |
|-------|--------|
| **Objective** | Rate rider climbing ability from mountain stage and summit finish results. |
| **Acceptance criteria** | Top climbers ranked higher than sprinters on 2023 data; rating updates after each relevant stage. |
| **Dependencies** | M4-01 |
| **Labels** | `milestone-4`, `area:model`, `complexity:M` |

### Issue M4-03: Sprint rating

| Field | Detail |
|-------|--------|
| **Objective** | Rate sprint ability from flat stage and bunch sprint results. |
| **Acceptance criteria** | Known sprinters rank in top decile; tested on 2023 flat stages. |
| **Dependencies** | M4-01 |
| **Labels** | `milestone-4`, `area:model`, `complexity:M` |

### Issue M4-04: TT rating

| Field | Detail |
|-------|--------|
| **Objective** | Rate time trial ability from individual and team TT results. |
| **Acceptance criteria** | TT specialists rank appropriately; team TT handled separately or documented. |
| **Dependencies** | M4-01 |
| **Labels** | `milestone-4`, `area:model`, `complexity:M` |

### Issue M4-05: Endurance, recovery, descending, explosiveness ratings

| Field | Detail |
|-------|--------|
| **Objective** | Complete the multi-dimensional rating vector. |
| **Description** | Endurance from multi-day consistency; recovery from post-rest performance; descending from relevant stages; explosiveness from short climbs and attacks. |
| **Acceptance criteria** | All four ratings computed and persisted; sanity checks documented. |
| **Dependencies** | M4-02, M4-03, M4-04 |
| **Labels** | `milestone-4`, `area:model`, `complexity:L` |

### Issue M4-06: Current form rating

| Field | Detail |
|-------|--------|
| **Objective** | Capture short-term performance trend. |
| **Description** | Exponentially decayed recent results weighted by stage importance. |
| **Acceptance criteria** | Form peaks align with known hot streaks; decays over inactive periods. |
| **Dependencies** | M4-01 |
| **Labels** | `milestone-4`, `area:model`, `complexity:M` |

### Issue M4-07: Rating pipeline and persistence

| Field | Detail |
|-------|--------|
| **Objective** | Batch recompute ratings across historical data. |
| **Description** | Prefect flow: chronological replay of results → rating updates → Parquet + PostgreSQL storage. |
| **Acceptance criteria** | Full rating history for 2015–2024; point-in-time ratings queryable at any stage. |
| **Dependencies** | M4-02 through M4-06 |
| **Labels** | `milestone-4`, `area:model`, `complexity:M` |

### Issue M4-08: Rating evaluation and visualization

| Field | Detail |
|-------|--------|
| **Objective** | Validate ratings against intuition and outcomes. |
| **Description** | Top-N accuracy per discipline, rating distribution plots, example rider trajectories. |
| **Acceptance criteria** | Evaluation notebook or script committed; summary in docs. |
| **Dependencies** | M4-07 |
| **Labels** | `milestone-4`, `area:docs`, `complexity:S` |

---

## Milestone 5 — Prediction Models

Progressive model ladder: baseline → classical ML → ensemble. Separate models per target.

### Issue M5-01: ML training framework and baselines

| Field | Detail |
|-------|--------|
| **Objective** | Shared training infrastructure with random and logistic baselines. |
| **Description** | `PredictionModel` port, train/eval split by time, MLflow logging, metrics module. |
| **Acceptance criteria** | Random and logistic baselines trained on stage winner task; metrics logged to MLflow. |
| **Dependencies** | Milestone 4 complete |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-02: Stage winner model — Random Forest

| Field | Detail |
|-------|--------|
| **Objective** | First tree-based stage winner model. |
| **Acceptance criteria** | Beats logistic baseline on log-loss; feature importance logged. |
| **Dependencies** | M5-01 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-03: Stage winner model — LightGBM

| Field | Detail |
|-------|--------|
| **Objective** | Gradient boosting stage winner model. |
| **Acceptance criteria** | Beats RF on held-out editions; hyperparams logged in MLflow. |
| **Dependencies** | M5-02 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-04: Stage winner model — CatBoost

| Field | Detail |
|-------|--------|
| **Objective** | CatBoost variant for categorical feature handling. |
| **Acceptance criteria** | Compared head-to-head with LightGBM; results in experiment tracker. |
| **Dependencies** | M5-03 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-05: Stage winner model — XGBoost

| Field | Detail |
|-------|--------|
| **Objective** | Complete boosting model comparison. |
| **Acceptance criteria** | Best stage winner model identified and tagged in MLflow. |
| **Dependencies** | M5-04 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-06: GC winner model

| Field | Detail |
|-------|--------|
| **Objective** | Predict overall Tour winner probabilities. |
| **Description** | Edition-level features, GC standings trajectory, same model ladder as stage winner. |
| **Acceptance criteria** | GC predictions for TDF 2023 test fold; Brier score and log-loss reported. |
| **Dependencies** | M5-01 |
| **Labels** | `milestone-5`, `area:model`, `complexity:L` |

### Issue M5-07: Podium probability model

| Field | Detail |
|-------|--------|
| **Objective** | Predict P(top-3) per rider. |
| **Acceptance criteria** | Calibrated probabilities; top predicted riders overlap actual podium > random. |
| **Dependencies** | M5-01 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-08: Top-10 probability model

| Field | Detail |
|-------|--------|
| **Objective** | Predict P(top-10) per rider. |
| **Acceptance criteria** | NDCG@10 reported; compared to baseline. |
| **Dependencies** | M5-01 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-09: Probability calibration

| Field | Detail |
|-------|--------|
| **Objective** | Calibrate raw model outputs. |
| **Description** | Platt scaling and isotonic regression; expected calibration error (ECE) before/after. |
| **Acceptance criteria** | ECE improves on validation set; calibration plots in MLflow artifacts. |
| **Dependencies** | M5-03 or best stage model |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-10: Model promotion workflow

| Field | Detail |
|-------|--------|
| **Objective** | Promote best MLflow run to production registry. |
| **Description** | Promotion criteria, model versioning, metadata in PostgreSQL. |
| **Acceptance criteria** | `make promote-model TARGET=stage_winner` promotes tagged model; rollback documented. |
| **Dependencies** | M5-09 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

### Issue M5-11: Inference pipeline

| Field | Detail |
|-------|--------|
| **Objective** | Generate predictions for a live or historical stage. |
| **Description** | Load production model, assemble features, output rider probabilities, persist `Prediction` entity. |
| **Acceptance criteria** | Inference for TDF 2023 stage 18 completes in < 30s locally; output validated. |
| **Dependencies** | M5-10 |
| **Labels** | `milestone-5`, `area:model`, `complexity:M` |

---

## Milestone 6 — Simulation Engine

Monte Carlo Tour simulation using prediction models and race state.

### Issue M6-01: Race state machine

| Field | Detail |
|-------|--------|
| **Objective** | Model Tour progression stage-by-stage. |
| **Description** | State: GC standings, points, active riders, jerseys, eliminated riders. |
| **Acceptance criteria** | State transitions match official rules; unit tests for GC time aggregation. |
| **Dependencies** | Milestone 5 complete |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:L` |

### Issue M6-02: Monte Carlo engine core

| Field | Detail |
|-------|--------|
| **Objective** | Run N independent Tour simulations. |
| **Description** | Sample stage outcomes from model probabilities, update state, aggregate GC/podium distributions. |
| **Acceptance criteria** | 10,000 simulations of TDF 2023 complete in acceptable time; reproducible with seed. |
| **Dependencies** | M6-01, M5-11 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:L` |

### Issue M6-03: Tactical events module

| Field | Detail |
|-------|--------|
| **Objective** | Model breakaways, peloton splits, team tactics. |
| **Description** | Probabilistic tactical events modifying stage outcome distributions. |
| **Acceptance criteria** | Events configurable; documented assumptions; disabled by default for baseline sim. |
| **Dependencies** | M6-02 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:M` |

### Issue M6-04: Abandonment model

| Field | Detail |
|-------|--------|
| **Objective** | Simulate rider DNFs across the Tour. |
| **Description** | DNF probability from fatigue, crash proxy, stage difficulty. |
| **Acceptance criteria** | Simulated DNF rate within reasonable range of historical average. |
| **Dependencies** | M6-02 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:M` |

### Issue M6-05: Weather effects in simulation

| Field | Detail |
|-------|--------|
| **Objective** | Modulate stage probabilities by weather scenario. |
| **Description** | Apply weather feature shifts to sampled outcomes; support hypothetical weather. |
| **Acceptance criteria** | Rain scenario measurably shifts outcomes; API for weather override. |
| **Dependencies** | M6-02 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:M` |

### Issue M6-06: Simulation output aggregation and storage

| Field | Detail |
|-------|--------|
| **Objective** | Persist and summarize simulation results. |
| **Description** | GC win%, podium%, top-10%, expected final GC position per rider. `Simulation` entity. |
| **Acceptance criteria** | Results queryable; Parquet export for dashboard. |
| **Dependencies** | M6-02 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:M` |

### Issue M6-07: Simulation validation against historical Tours

| Field | Detail |
|-------|--------|
| **Objective** | Verify simulations produce realistic distributions. |
| **Description** | Compare simulated vs actual GC for held-out editions; coverage metrics. |
| **Acceptance criteria** | Actual winner falls within reasonable probability mass; documented in evaluation report. |
| **Dependencies** | M6-06 |
| **Labels** | `milestone-6`, `area:simulation`, `complexity:M` |

---

## Milestone 7 — REST API

FastAPI service exposing predictions, simulations, and ratings.

### Issue M7-01: FastAPI application scaffold

| Field | Detail |
|-------|--------|
| **Objective** | Production-ready API skeleton. |
| **Description** | App factory, dependency injection, lifespan hooks, CORS, structured logging. |
| **Acceptance criteria** | `uvicorn` starts via Docker; OpenAPI schema auto-generated. |
| **Dependencies** | Milestone 5 complete (M6 for simulation endpoints) |
| **Labels** | `milestone-7`, `area:api`, `complexity:S` |

### Issue M7-02: Health and metadata endpoints

| Field | Detail |
|-------|--------|
| **Objective** | Operational endpoints for monitoring. |
| **Description** | `GET /health`, `GET /ready`, `GET /version`, model metadata. |
| **Acceptance criteria** | Health checks used in Docker Compose; return model version and data freshness. |
| **Dependencies** | M7-01 |
| **Labels** | `milestone-7`, `area:api`, `complexity:XS` |

### Issue M7-03: Stage prediction endpoints

| Field | Detail |
|-------|--------|
| **Objective** | Serve stage winner probabilities. |
| **Description** | `GET /editions/{year}/stages/{number}/predictions/stage-winner` |
| **Acceptance criteria** | Returns ranked rider probabilities; integration tests with test DB. |
| **Dependencies** | M7-01, M5-11 |
| **Labels** | `milestone-7`, `area:api`, `complexity:M` |

### Issue M7-04: GC, podium, and top-10 endpoints

| Field | Detail |
|-------|--------|
| **Objective** | Serve edition-level prediction endpoints. |
| **Acceptance criteria** | Three endpoints live; consistent response schema. |
| **Dependencies** | M7-01, M5-06, M5-07, M5-08 |
| **Labels** | `milestone-7`, `area:api`, `complexity:M` |

### Issue M7-05: Simulation endpoints

| Field | Detail |
|-------|--------|
| **Objective** | Trigger and retrieve Monte Carlo simulations. |
| **Description** | `POST /editions/{year}/simulations`, `GET /simulations/{id}` |
| **Acceptance criteria** | Async job pattern or sync with timeout; results match engine output. |
| **Dependencies** | M7-01, M6-06 |
| **Labels** | `milestone-7`, `area:api`, `complexity:M` |

### Issue M7-06: Rider rating and ranking endpoints

| Field | Detail |
|-------|--------|
| **Objective** | Expose rating engine output via API. |
| **Description** | `GET /riders/{id}/ratings`, `GET /ratings/leaderboard?discipline=climbing` |
| **Acceptance criteria** | Point-in-time ratings queryable by stage; pagination supported. |
| **Dependencies** | M7-01, M4-07 |
| **Labels** | `milestone-7`, `area:api`, `complexity:S` |

### Issue M7-07: API authentication and rate limiting

| Field | Detail |
|-------|--------|
| **Objective** | Protect API in production. |
| **Description** | API key auth via header; slowapi rate limiting. |
| **Acceptance criteria** | Invalid key returns 401; rate limit returns 429; disabled in local dev via env. |
| **Dependencies** | M7-01 |
| **Labels** | `milestone-7`, `area:api`, `complexity:M` |

### Issue M7-08: OpenAPI docs and API integration tests

| Field | Detail |
|-------|--------|
| **Objective** | Document and test the full API surface. |
| **Acceptance criteria** | All endpoints in OpenAPI; integration test suite in CI. |
| **Dependencies** | M7-02 through M7-06 |
| **Labels** | `milestone-7`, `area:api`, `complexity:S` |

---

## Milestone 8 — Dashboard

Next.js frontend with predictions, charts, maps, and simulation viewer.

### Issue M8-01: Next.js project scaffold with Tailwind

| Field | Detail |
|-------|--------|
| **Objective** | Frontend app in monorepo `frontend/`. |
| **Description** | Next.js 14+, TypeScript, Tailwind, ESLint, API client module. |
| **Acceptance criteria** | `npm run dev` works; connects to local API; included in Docker Compose. |
| **Dependencies** | M7-01 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:S` |

### Issue M8-02: Race overview and stage list

| Field | Detail |
|-------|--------|
| **Objective** | Landing page for a Tour edition. |
| **Acceptance criteria** | Lists 21 stages with type, date, distance; links to stage detail. |
| **Dependencies** | M8-01 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:M` |

### Issue M8-03: Prediction probability charts (D3)

| Field | Detail |
|-------|--------|
| **Objective** | Visualize rider win probabilities. |
| **Description** | Horizontal bar chart, top-N toggle, stage vs GC views. |
| **Acceptance criteria** | Renders from live API; responsive layout. |
| **Dependencies** | M8-01, M7-03 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:M` |

### Issue M8-04: Stage explorer with Mapbox profile map

| Field | Detail |
|-------|--------|
| **Objective** | Interactive stage detail with elevation/route map. |
| **Acceptance criteria** | Mapbox map with stage metadata; profile chart if data available. |
| **Dependencies** | M8-02 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:L` |

### Issue M8-05: Simulation viewer

| Field | Detail |
|-------|--------|
| **Objective** | Display Monte Carlo outcome distributions. |
| **Description** | GC win heatmap, podium probability table, run simulation button. |
| **Acceptance criteria** | Polls simulation endpoint; shows progress for long runs. |
| **Dependencies** | M8-01, M7-05 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:M` |

### Issue M8-06: Rider rating leaderboard

| Field | Detail |
|-------|--------|
| **Objective** | Browse riders by discipline rating. |
| **Acceptance criteria** | Sortable table; discipline filter; links to rider detail. |
| **Dependencies** | M8-01, M7-06 |
| **Labels** | `milestone-8`, `area:frontend`, `complexity:S` |

---

## Milestone 9 — Evaluation

Rigorous offline evaluation, calibration analysis, and model comparison.

### Issue M9-01: Time-series cross-validation framework

| Field | Detail |
|-------|--------|
| **Objective** | Prevent temporal leakage in all evaluations. |
| **Description** | Walk-forward splits by edition; configurable train/test windows. |
| **Acceptance criteria** | Used by all M5 training scripts; documented split strategy. |
| **Dependencies** | Milestone 5 complete |
| **Labels** | `milestone-9`, `area:model`, `complexity:M` |

### Issue M9-02: Metrics dashboard (MLflow + custom)

| Field | Detail |
|-------|--------|
| **Objective** | Central view of model performance over time. |
| **Acceptance criteria** | Key metrics per model/target visible in MLflow or custom HTML report. |
| **Dependencies** | M9-01 |
| **Labels** | `milestone-9`, `area:model`, `complexity:M` |

### Issue M9-03: Calibration analysis

| Field | Detail |
|-------|--------|
| **Objective** | Systematic calibration reporting. |
| **Description** | Reliability diagrams, ECE, Brier decomposition per target. |
| **Acceptance criteria** | Report generated for all production models; committed to docs/evaluation. |
| **Dependencies** | M5-09 |
| **Labels** | `milestone-9`, `area:model`, `complexity:M` |

### Issue M9-04: Feature importance reporting

| Field | Detail |
|-------|--------|
| **Objective** | Explain model decisions. |
| **Description** | SHAP or native feature importance per model; top features documented. |
| **Acceptance criteria** | Importance plots in MLflow artifacts; summary in feature catalog. |
| **Dependencies** | M5-03+ |
| **Labels** | `milestone-9`, `area:model`, `complexity:S` |

### Issue M9-05: Model comparison and ablation studies

| Field | Detail |
|-------|--------|
| **Objective** | Quantify value of each modeling decision. |
| **Description** | Compare model ladder steps; ablate feature groups (ratings, weather, fatigue). |
| **Acceptance criteria** | Ablation table in docs; every improvement measurable vs baseline. |
| **Dependencies** | M9-01, M9-04 |
| **Labels** | `milestone-9`, `area:model`, `complexity:M` |

---

## Milestone 10 — Production

Monitoring, caching, deployment, and portfolio polish.

### Issue M10-01: Structured logging and observability

| Field | Detail |
|-------|--------|
| **Objective** | Production-grade logging across API, pipelines, and models. |
| **Description** | JSON structured logs, request IDs, pipeline run correlation. |
| **Acceptance criteria** | All services emit structured logs; log levels configurable via env. |
| **Dependencies** | Milestones 7–8 complete |
| **Labels** | `milestone-10`, `area:infra`, `complexity:M` |

### Issue M10-02: Redis caching layer

| Field | Detail |
|-------|--------|
| **Objective** | Cache hot prediction endpoints. |
| **Description** | Redis in Docker Compose; cache keyed by edition/stage/model version. |
| **Acceptance criteria** | Cache hit reduces latency > 50%; TTL and invalidation documented. |
| **Dependencies** | M7-03 |
| **Labels** | `milestone-10`, `area:infra`, `complexity:M` |

### Issue M10-03: Production Docker and deployment docs

| Field | Detail |
|-------|--------|
| **Objective** | Document path from local dev to deployed system. |
| **Description** | Multi-stage Dockerfiles, env var reference, deployment ADR. |
| **Acceptance criteria** | `docs/deployment.md` complete; CI builds production images. |
| **Dependencies** | M1 Docker, M7 API, M8 frontend |
| **Labels** | `milestone-10`, `area:infra`, `complexity:M` |

### Issue M10-04: Portfolio polish

| Field | Detail |
|-------|--------|
| **Objective** | Make the repository portfolio-ready. |
| **Description** | Demo dataset, architecture screenshots, README badges, example predictions, video/GIF optional. |
| **Acceptance criteria** | New contributor can understand system in 10 minutes from README alone. |
| **Dependencies** | All prior milestones |
| **Labels** | `milestone-10`, `area:docs`, `complexity:M` |

---

## Promoting Issues to GitHub

When ready to start a milestone:

1. Create a GitHub Milestone (e.g. "M2 — Historical Data Ingestion").
2. Copy issues from this file into GitHub using `scripts/create-github-issues.sh` (extend for each milestone).
3. Add issues to the YellowMind Project board: Backlog → Ready.
