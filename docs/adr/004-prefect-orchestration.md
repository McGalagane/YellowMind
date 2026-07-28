# ADR-004: Prefect for pipeline orchestration

## Status

Accepted

## Context

YellowMind needs scheduled, retriable pipelines for ingestion, feature generation, rating updates, and model training. The orchestrator must be Python-native and run locally with Docker.

## Decision

Use **Prefect 2.x** for all data and ML pipelines.

## Consequences

- **Easier:** Python-native flows; good local dev experience; observable runs in Prefect UI
- **Harder:** Additional service in Docker Compose; team must learn Prefect patterns

## Alternatives considered

- **Apache Airflow** — rejected; heavier operational overhead for a solo/small team project
- **Plain scripts + cron** — rejected; no retry, observability, or dependency management
