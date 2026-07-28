# ADR-006: Baseline-first model progression

## Status

Accepted

## Context

It is tempting to jump directly to gradient boosting or neural networks. Without baselines, it is impossible to prove that complexity adds value — a critical portfolio requirement.

## Decision

Every prediction target must follow this progression, with measurable improvement at each step:

```
Random → Logistic Regression → Random Forest → LightGBM → CatBoost → XGBoost → Deep Learning → Ensemble → Monte Carlo
```

No step may be skipped. Each step's metrics are logged to MLflow before proceeding.

## Consequences

- **Easier:** Defensible model choices; clear ablation story for portfolio reviewers
- **Harder:** More implementation work before reaching "impressive" models

## Alternatives considered

- **Start with LightGBM** — rejected; no baseline comparison
- **Neural networks first** — rejected; wrong inductive bias for tabular stage-level data at MVP
