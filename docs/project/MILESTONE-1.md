# Milestone 1 — Project Foundation

Repository setup, tooling, CI, Docker, documentation, architecture, and domain scaffolding.

**Target:** Bootstrappable monorepo ready for data ingestion work (M2).

**Sprint order:**

| Order | Issue | Title | Complexity |
|-------|-------|-------|------------|
| 1 | #1 | Initialize Poetry project and package structure | S |
| 2 | #2 | Configure Ruff, Pyright, and pre-commit | S |
| 3 | #3 | GitHub Actions CI pipeline | S |
| 4 | #5 | Architecture documentation and ADR framework | M |
| 5 | #6 | Domain entity scaffolding | M |
| 6 | #4 | Docker Compose local development environment | M |
| 7 | #7 | PostgreSQL schema migrations | M |

---

## Issue #1: Initialize Poetry project and package structure

**Labels:** `milestone-1`, `area:infra`, `complexity:S`

### Objective

Bootstrappable Python package with typed, linted codebase following Clean Architecture layout.

### Description

Create `pyproject.toml`, `src/yellowmind/` with empty packages:

- `domain/` — entities, value objects, repository interfaces
- `application/` — use cases, DTOs
- `infrastructure/` — adapters (empty for now)
- `presentation/` — API and CLI entry points (empty for now)

### Acceptance criteria

- [ ] `poetry install` succeeds on Python 3.12
- [ ] `from yellowmind import __version__` works
- [ ] Package follows src layout
- [ ] `tests/` directory with one smoke test

### Technical notes

- Python `^3.12`
- Package name: `yellowmind`
- Dev deps stub: pytest (full tooling in #2)
- No application logic yet — structure only

### Dependencies

None

### Files to create/modify

```
pyproject.toml
src/yellowmind/__init__.py
src/yellowmind/domain/__init__.py
src/yellowmind/application/__init__.py
src/yellowmind/infrastructure/__init__.py
src/yellowmind/presentation/__init__.py
tests/unit/test_version.py
```

---

## Issue #2: Configure Ruff, Pyright, and pre-commit

**Labels:** `milestone-1`, `area:infra`, `complexity:S`

### Objective

Enforce code quality on every commit.

### Description

Add Ruff (lint + format), Pyright (strict mode for `src/`), and pre-commit hooks.

### Acceptance criteria

- [ ] `poetry run ruff check .` passes
- [ ] `poetry run ruff format --check .` passes
- [ ] `poetry run pyright` passes
- [ ] `pre-commit run --all-files` passes

### Technical notes

- Ruff replaces black, isort, flake8
- Pyright `typeCheckingMode: strict` for `src/yellowmind`
- pre-commit hooks: ruff, ruff-format, pyright, trailing-whitespace, end-of-file-fixer

### Dependencies

#1

### Files to create/modify

```
ruff.toml
pyrightconfig.json
.pre-commit-config.yaml
pyproject.toml  (add dev dependencies)
```

---

## Issue #3: GitHub Actions CI pipeline

**Labels:** `milestone-1`, `area:infra`, `complexity:S`

### Objective

Automated lint, type-check, and test on every PR.

### Description

Workflow triggered on push to `main` and all pull requests.

### Acceptance criteria

- [ ] CI runs: checkout → Poetry install → ruff → pyright → pytest
- [ ] Coverage report uploaded (optional codecov, can defer upload)
- [ ] Workflow badge in README (added in #5)

### Technical notes

- Use `actions/setup-python` with 3.12
- Cache Poetry virtualenv
- Fail fast on lint before tests

### Dependencies

#1, #2

### Files to create/modify

```
.github/workflows/ci.yml
```

---

## Issue #4: Docker Compose local development environment

**Labels:** `milestone-1`, `area:infra`, `complexity:M`

### Objective

Full local stack starts with one command.

### Description

Docker Compose services:

- **postgres** — PostgreSQL 16, persistent volume
- **mlflow** — MLflow tracking server
- **api** — FastAPI stub (health endpoint only until M7)
- **prefect** — Prefect server (or agent stub)

Provide `scripts/dev.sh` and `Makefile` targets: `up`, `down`, `logs`, `migrate`.

### Acceptance criteria

- [ ] `make up` starts all services
- [ ] `make down` tears down cleanly
- [ ] PostgreSQL health check passes
- [ ] MLflow UI reachable at documented port
- [ ] API stub returns 200 on `/health`

### Technical notes

- Env vars via `.env.example` (committed), `.env` (gitignored)
- Multi-stage Dockerfile for API (Python 3.12 slim)
- Network: single compose network `yellowmind`

### Dependencies

#1

### Files to create/modify

```
docker/Dockerfile.api
docker-compose.yml
.env.example
scripts/dev.sh
Makefile
```

---

## Issue #5: Architecture documentation and ADR framework

**Labels:** `milestone-1`, `area:docs`, `complexity:M`

### Objective

Document system design before feature work begins.

### Description

Expand README, add architecture docs, ADR template, and initial ADRs reflecting validated decisions.

### Acceptance criteria

- [ ] README: vision, stack, quickstart (`make up`), project structure
- [ ] `docs/architecture/overview.md` with C4 context + container diagrams (Mermaid)
- [ ] `docs/adr/000-template.md` and ADR-001 through ADR-007
- [ ] ERD diagram in `docs/architecture/erd.md`
- [ ] CI badge in README

### Technical notes

Initial ADRs:

| ADR | Title |
|-----|-------|
| 001 | Clean Architecture layer split |
| 002 | PostgreSQL + DuckDB dual storage |
| 003 | PCS as primary data source |
| 004 | Prefect for pipeline orchestration |
| 005 | MLflow for experiment tracking |
| 006 | Baseline-first model progression |
| 007 | Monorepo with Poetry |

### Dependencies

#1

### Files to create/modify

```
README.md
docs/architecture/overview.md
docs/architecture/erd.md
docs/adr/000-template.md
docs/adr/001-clean-architecture.md
docs/adr/002-dual-storage.md
docs/adr/003-pcs-data-source.md
docs/adr/004-prefect-orchestration.md
docs/adr/005-mlflow-tracking.md
docs/adr/006-baseline-first-models.md
docs/adr/007-monorepo-poetry.md
```

---

## Issue #6: Domain entity scaffolding

**Labels:** `milestone-1`, `area:infra`, `complexity:M`

### Objective

Typed domain models for all core entities with validation rules.

### Description

Implement domain entities (dataclasses or Pydantic models in domain layer — ADR if Pydantic in domain):

- `Rider`, `Team`, `Stage`, `TourEdition`
- `RaceResult`, `Weather`, `StageProfile`
- `Prediction`, `Simulation`, `RiderRating`, `TeamStrategy`

Define abstract repository interfaces in `domain/repositories/`. No database or ORM imports.

### Acceptance criteria

- [ ] All 11 entities defined with complete type hints
- [ ] Validation rules tested (e.g. stage number 1–21, probabilities sum to 1)
- [ ] Zero imports from infrastructure/presentation in `domain/`
- [ ] Unit test coverage for each entity

### Technical notes

- Use value objects where appropriate: `StageNumber`, `Probability`, `Distance`
- Repository interfaces: `RiderRepository`, `StageRepository`, etc.

### Dependencies

#1, #2

### Files to create/modify

```
src/yellowmind/domain/entities/
src/yellowmind/domain/value_objects/
src/yellowmind/domain/repositories/
tests/unit/domain/
```

---

## Issue #7: PostgreSQL schema migrations

**Labels:** `milestone-1`, `area:infra`, `complexity:M`

### Objective

Persistent operational storage with Alembic migrations.

### Description

SQLAlchemy 2.0 models mirroring domain entities. Alembic migrations. Repository implementations for core entities.

### Acceptance criteria

- [ ] `make migrate` applies all migrations against Docker PostgreSQL
- [ ] Integration test: insert and read `Rider`, `Stage`, `RaceResult`
- [ ] Foreign keys enforce entity relationships from ERD

### Technical notes

- Sync SQLAlchemy for M1 (async optional later)
- Connection string from env: `DATABASE_URL`
- Seed script optional — defer to M2

### Dependencies

#4, #6

### Files to create/modify

```
src/yellowmind/infrastructure/persistence/
alembic.ini
alembic/versions/
tests/integration/persistence/
Makefile  (add migrate target)
```

---

## GitHub Project board

When issues are created, add all to the **YellowMind** project:

| Column | Issues |
|--------|--------|
| Backlog | #4, #5, #6, #7 |
| Ready | #1 |
| In Progress | — |
| Review | — |
| Done | — |

Move #1 → In Progress when starting implementation. Each PR closes exactly one issue.
