# ADR-005: MLflow for experiment tracking

## Status

Accepted

## Context

YellowMind will train many model variants (baselines through ensembles) across multiple prediction targets. Results must be reproducible, comparable, and promotable to production.

## Decision

Use **MLflow** for experiment tracking, parameter logging, metric comparison, and model registry.

## Consequences

- **Easier:** Side-by-side model comparison; artifact storage; production promotion workflow
- **Harder:** MLflow server in Docker Compose; artifact storage configuration for production

## Alternatives considered

- **Weights & Biases** — excellent but cloud-dependent; MLflow chosen for local-first reproducibility
- **Custom JSON logs** — rejected; does not scale across model ladder
