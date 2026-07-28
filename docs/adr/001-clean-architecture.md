# ADR-001: Clean Architecture layer split

## Status

Accepted

## Context

YellowMind is a multi-year portfolio project spanning data ingestion, ML, simulation, API, and frontend. Without strict boundaries, business logic leaks into FastAPI routes and SQLAlchemy models, making testing and model iteration painful.

## Decision

Organize Python code into four layers under `src/yellowmind/`:

1. **Domain** — entities, value objects, repository interfaces, pure domain services
2. **Application** — use cases and DTOs orchestrating domain logic
3. **Infrastructure** — database adapters, PCS client, ML wrappers, Prefect tasks
4. **Presentation** — FastAPI routers and CLI entry points

Dependencies flow inward only. Domain has zero imports from outer layers.

## Consequences

- **Easier:** Unit testing domain logic without DB or HTTP; swapping LightGBM for CatBoost without touching API
- **Harder:** More boilerplate (interfaces, adapters); requires discipline on every PR

## Alternatives considered

- **Flat package structure** — rejected; does not scale across 10 milestones
- **Hexagonal architecture naming** — equivalent; Clean Architecture chosen for wider recognition
