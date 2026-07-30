# Entity-Relationship Diagram

Core entities and their relationships for YellowMind.

`Rider` holds identity only, while `RiderParticipation` holds the facts that are true of a rider for one edition: team, bib number, age, and how the race ended. See [ADR-009](../adr/009-rider-identity-and-participation.md) for why the two are separate.

## ERD

```mermaid
erDiagram
    TourEdition ||--o{ Stage : contains
    TourEdition ||--o{ Team : participates
    TourEdition ||--o{ RiderParticipation : registers
    Rider ||--o{ RiderParticipation : enters
    Team ||--o{ RiderParticipation : fields
    Stage ||--|| StageProfile : has
    Stage ||--o| Weather : has
    Stage ||--o{ RaceResult : produces
    Rider ||--o{ RaceResult : achieves
    Rider ||--o{ RiderRating : has
    TourEdition ||--o{ Prediction : generates
    TourEdition ||--o{ Simulation : runs
    Team ||--o| TeamStrategy : defines

    TourEdition {
        uuid id PK
        int year
        string name
        date start_date
        date end_date
    }

    Stage {
        uuid id PK
        uuid tour_edition_id FK
        int number
        date date
        string type
        float distance_km
    }

    StageProfile {
        uuid id PK
        uuid stage_id FK
        float elevation_gain_m
        string finish_type
        int profile_score
    }

    Team {
        uuid id PK
        uuid tour_edition_id FK
        string name
        string source_slug
        string nationality "nullable"
    }

    Rider {
        uuid id PK
        string name
        string nationality
        string source_slug UK
        date birth_date "nullable"
    }

    RiderParticipation {
        uuid id PK
        uuid tour_edition_id FK
        uuid rider_id FK
        uuid team_id FK
        int bib_number
        int age "nullable"
        int final_gc_position "nullable"
        string abandonment_kind "nullable"
        int abandonment_stage "nullable"
        bool is_young_rider
    }

    RaceResult {
        uuid id PK
        uuid stage_id FK
        uuid rider_id FK
        int rank
        string time
        int time_gap_seconds
        string status
    }

    Weather {
        uuid id PK
        uuid stage_id FK
        float temperature_c
        float wind_speed_kmh
        float precipitation_mm
    }

    RiderRating {
        uuid id PK
        uuid rider_id FK
        uuid stage_id FK
        float climbing
        float sprint
        float tt
        float endurance
        float recovery
        float descending
        float explosiveness
        float form
    }

    Prediction {
        uuid id PK
        uuid tour_edition_id FK
        uuid stage_id FK
        string target
        json probabilities
        datetime created_at
    }

    Simulation {
        uuid id PK
        uuid tour_edition_id FK
        int n_iterations
        json outcomes
        datetime created_at
    }

    TeamStrategy {
        uuid id PK
        uuid team_id FK
        uuid gc_leader_id FK
        string approach
    }
```

## Storage mapping

| Entity group | Primary store | Rationale |
|-------------|---------------|-----------|
| TourEdition, Stage, Rider, RiderParticipation, Team, RaceResult | PostgreSQL | Operational queries, API serving |
| Feature matrices, training data | DuckDB / Parquet | Columnar scans, reproducible ML |
| Model artifacts | MLflow | Versioned experiments and promotion |
| Predictions, Simulations | PostgreSQL | Audit trail, API history |

See [ADR-002: Dual storage](../adr/002-dual-storage.md).
