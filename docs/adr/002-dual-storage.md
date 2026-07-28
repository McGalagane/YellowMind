# ADR-002: PostgreSQL and DuckDB dual storage

## Status

Accepted

## Context

YellowMind serves predictions via API (transactional, relational queries) and trains models on large historical feature matrices (columnar, scan-heavy). A single database cannot optimize both workloads.

## Decision

Use **PostgreSQL** for operational entities (riders, stages, results, predictions) and **DuckDB over Parquet** for analytical workloads (feature stores, training datasets).

## Consequences

- **Easier:** Fast API queries with FK integrity; reproducible ML datasets as versioned Parquet files
- **Harder:** Two storage systems to maintain; explicit ETL between silver PostgreSQL and gold Parquet

## Alternatives considered

- **PostgreSQL only** — rejected; poor performance for large feature matrix scans
- **DuckDB only** — rejected; lacks mature operational tooling for serving and migrations
