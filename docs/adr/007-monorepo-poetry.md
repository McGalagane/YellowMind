# ADR-007: Monorepo with Poetry

## Status

Accepted

## Context

YellowMind spans Python backend, ML pipelines, and a Next.js frontend. Dependency management, tooling, and CI must be reproducible across contributors and portfolio reviewers.

## Decision

Use a **monorepo** with:

- **Poetry** for Python dependency management and packaging
- **Ruff** for linting and formatting
- **Pyright** for strict static typing
- **pre-commit** for local quality gates
- **frontend/** for Next.js (npm, separate from Poetry)

## Consequences

- **Easier:** Single clone runs everything; lockfile reproducibility; unified CI
- **Harder:** Poetry learning curve; Python/Node dual toolchain

## Alternatives considered

- **pip + requirements.txt** — rejected; no lockfile discipline by default
- **Separate repos** — rejected; poor portfolio cohesion
