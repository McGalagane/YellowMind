# Architecture Overview

YellowMind follows **Clean Architecture** with a **domain-driven** core. Dependencies point inward: presentation and infrastructure depend on application and domain, never the reverse.

## Context diagram (C4 Level 1)

```mermaid
flowchart TB
    User[User / Portfolio Reviewer]
    Wiki[Wikipedia REST API]
    Weather[Open-Meteo Archive API]

    YM[YellowMind Platform]

    User -->|predictions, simulations| YM
    YM -->|historical results| Wiki
    YM -->|stage weather| Weather
```

## Container diagram (C4 Level 2)

```mermaid
flowchart TB
    subgraph Client
        WEB[Next.js Dashboard]
    end

    subgraph YellowMind
        API[FastAPI REST API]
        PREF[Prefect Pipelines]
        FEAT[Feature Engine]
        RATE[Rating Engine]
        ML[Prediction Models]
        SIM[Monte Carlo Simulator]
    end

    subgraph Storage
        PG[(PostgreSQL)]
        DDB[(DuckDB / Parquet)]
        MLF[MLflow]
    end

    WEB --> API
    API --> PG
    API --> DDB
    API --> ML
    PREF --> ING[Wikipedia Ingestion]
    ING --> DDB
    PREF --> PG
    FEAT --> DDB
    RATE --> DDB
    ML --> MLF
    ML --> DDB
    SIM --> ML
    SIM --> PG
```

## Layer responsibilities

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Domain | `domain/` | Entities, value objects, domain rules, repository interfaces |
| Application | `application/` | Use cases orchestrating domain logic via ports |
| Infrastructure | `infrastructure/` | PostgreSQL, DuckDB, ingestion clients, ML model adapters |
| Presentation | `presentation/` | FastAPI routes, CLI, request/response schemas |

## Data flow

```mermaid
sequenceDiagram
    participant WIKI as Wikipedia API
    participant P as Prefect
    participant BR as Bronze Parquet
    participant FE as Feature Engine
    participant ML as Training
    participant PG as PostgreSQL
    participant API as FastAPI

    WIKI->>P: Fetch results
    P->>BR: Raw normalized data
    BR->>FE: Historical features
    FE->>ML: Train/test matrices
    ML->>PG: Model metadata
    API->>PG: Serve predictions
    API->>BR: Inference features
```

## ML model progression

Every prediction target follows the same ladder — baselines are never skipped:

```
Random → Logistic Regression → Random Forest → LightGBM → CatBoost → XGBoost → Deep Learning → Ensemble → Monte Carlo
```

## Related documents

- [Entity-relationship diagram](erd.md)
- [ADR index](../adr/)
- [Project backlog](../project/BACKLOG.md)
