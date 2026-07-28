# YellowMind

[![CI](https://github.com/McGalagane/YellowMind/actions/workflows/ci.yml/badge.svg)](https://github.com/McGalagane/YellowMind/actions/workflows/ci.yml)

AI platform for Tour de France predictions: stage winners, General Classification (GC), podium and top-10 probabilities, and full Tour simulations via Monte Carlo.

## Vision

YellowMind is a production-grade machine learning system demonstrating software engineering, MLOps, data engineering, and AI skills. It predicts cycling outcomes using historical race data, multi-dimensional rider ratings, and progressively refined models.

## Tech stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, FastAPI |
| ML | scikit-learn, LightGBM, CatBoost, XGBoost, PyTorch |
| Data | PostgreSQL, DuckDB, Parquet, Pandas, Polars |
| Pipelines | Prefect |
| Experiments | MLflow |
| Frontend | Next.js, React, TypeScript, Tailwind, D3.js, Mapbox |
| Infra | Docker, GitHub Actions, Poetry, Ruff, Pyright |

## Quickstart

```bash
# Install dependencies
poetry install

# Run quality checks
poetry run ruff check .
poetry run pyright
poetry run pytest

# Install pre-commit hooks
poetry run pre-commit install
```

Full local stack (PostgreSQL, MLflow, API) via Docker Compose — see [Architecture overview](docs/architecture/overview.md).

## Project structure

```
src/yellowmind/
├── domain/           # Entities, value objects, repository interfaces
├── application/      # Use cases and DTOs
├── infrastructure/   # DB, ingestion, ML adapters
└── presentation/     # FastAPI and CLI

docs/
├── architecture/     # System design, ERD
├── adr/              # Architecture Decision Records
└── project/          # Milestone backlog

tests/
├── unit/
└── integration/
```

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Entity-relationship diagram](docs/architecture/erd.md)
- [ADR index](docs/adr/)
- [Project backlog (M2–M10)](docs/project/BACKLOG.md)
- [Milestone 1 spec](docs/project/MILESTONE-1.md)

## Data sources

| Source | Use | Licence |
|--------|-----|---------|
| [Wikipedia](https://en.wikipedia.org) REST API | Editions, stages, results, GC standings, teams, riders | CC BY-SA 4.0 |
| [Open-Meteo](https://open-meteo.com) Archive API | Historical stage weather | CC BY 4.0 |

Race data is derived from Wikipedia and is available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Stage results are ingested at **top-10 granularity** rather than full peloton. See
[ADR-008](docs/adr/008-open-data-sources.md) for why, and for the impact on the ML plan.

## Development workflow

1. Pick an issue from [Milestone 1](docs/project/MILESTONE-1.md).
2. Create a feature branch: `feat/<issue>-<short-description>`.
3. Implement with tests, types, and docs.
4. Open a PR — one issue per PR, one concern per commit.

## License

See [LICENSE](LICENSE).
