#!/usr/bin/env bash
# Create Milestone 1 GitHub issues for YellowMind.
# Prerequisites: gh auth login
set -euo pipefail

REPO="${GITHUB_REPO:-McGalagane/YellowMind}"

echo "Creating Milestone 1 on ${REPO}..."

MILESTONE_URL=$(gh api repos/"${REPO}"/milestones \
  --method POST \
  -f title="M1 — Project Foundation" \
  -f description="Repository setup, tooling, CI, Docker, documentation, architecture, and domain scaffolding." \
  -f state="open" \
  --jq '.html_url')

echo "Milestone created: ${MILESTONE_URL}"

create_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"

  gh issue create \
    --repo "${REPO}" \
    --title "${title}" \
    --body "${body}" \
    --label "${labels}" \
    --milestone "M1 — Project Foundation"
}

# Issue #1
create_issue \
  "feat(infra): initialize Poetry project and package structure" \
  "$(cat <<'EOF'
## Objective
Bootstrappable Python package with typed, linted codebase following Clean Architecture layout.

## Description
Create `pyproject.toml`, `src/yellowmind/` with empty packages:
- `domain/` — entities, value objects, repository interfaces
- `application/` — use cases, DTOs
- `infrastructure/` — adapters (empty for now)
- `presentation/` — API and CLI entry points (empty for now)

## Acceptance criteria
- [ ] `poetry install` succeeds on Python 3.12
- [ ] `from yellowmind import __version__` works
- [ ] Package follows src layout
- [ ] `tests/` directory with one smoke test

## Technical notes
- Python `^3.12`
- Package name: `yellowmind`
- No application logic yet — structure only

## Dependencies
None

## Reference
See `docs/project/MILESTONE-1.md` Issue #1
EOF
)" \
  "milestone-1,area:infra,complexity:S"

# Issue #2
create_issue \
  "chore(infra): configure Ruff, Pyright, and pre-commit" \
  "$(cat <<'EOF'
## Objective
Enforce code quality on every commit.

## Description
Add Ruff (lint + format), Pyright (strict mode for `src/`), and pre-commit hooks.

## Acceptance criteria
- [ ] `poetry run ruff check .` passes
- [ ] `poetry run ruff format --check .` passes
- [ ] `poetry run pyright` passes
- [ ] `pre-commit run --all-files` passes

## Technical notes
- Ruff replaces black, isort, flake8
- Pyright `typeCheckingMode: strict` for `src/yellowmind`

## Dependencies
#1

## Reference
See `docs/project/MILESTONE-1.md` Issue #2
EOF
)" \
  "milestone-1,area:infra,complexity:S"

# Issue #3
create_issue \
  "chore(ci): add GitHub Actions CI pipeline" \
  "$(cat <<'EOF'
## Objective
Automated lint, type-check, and test on every PR.

## Description
Workflow triggered on push to `main` and all pull requests: Poetry install → ruff → pyright → pytest.

## Acceptance criteria
- [ ] CI runs on push to `main` and all PRs
- [ ] Failing lint or type-check blocks the workflow
- [ ] Tests run and pass on scaffold

## Dependencies
#1, #2

## Reference
See `docs/project/MILESTONE-1.md` Issue #3
EOF
)" \
  "milestone-1,area:infra,complexity:S"

# Issue #4
create_issue \
  "feat(infra): Docker Compose local development environment" \
  "$(cat <<'EOF'
## Objective
Full local stack starts with one command.

## Description
Docker Compose: PostgreSQL, MLflow, API stub, Prefect server. `make up` / `make down`.

## Acceptance criteria
- [ ] `make up` starts all services
- [ ] `make down` tears down cleanly
- [ ] PostgreSQL and MLflow health checks pass
- [ ] API stub returns 200 on `/health`

## Dependencies
#1

## Reference
See `docs/project/MILESTONE-1.md` Issue #4
EOF
)" \
  "milestone-1,area:infra,complexity:M"

# Issue #5
create_issue \
  "docs(readme): architecture documentation and ADR framework" \
  "$(cat <<'EOF'
## Objective
Document system design before feature work begins.

## Description
Expand README, add architecture docs, ADR template, ADR-001 through ADR-007, ERD diagram.

## Acceptance criteria
- [ ] README: vision, stack, quickstart, project structure
- [ ] Architecture overview with C4 diagrams
- [ ] At least 7 ADRs committed
- [ ] ERD diagram committed

## Dependencies
#1

## Reference
See `docs/project/MILESTONE-1.md` Issue #5
EOF
)" \
  "milestone-1,area:docs,complexity:M"

# Issue #6
create_issue \
  "feat(domain): domain entity scaffolding" \
  "$(cat <<'EOF'
## Objective
Typed domain models for all core entities with validation rules.

## Description
Entities: Rider, Team, Stage, TourEdition, RaceResult, Weather, StageProfile, Prediction, Simulation, RiderRating, TeamStrategy. Abstract repository interfaces. No DB yet.

## Acceptance criteria
- [ ] All 11 entities with complete type hints
- [ ] Validation rules unit tested
- [ ] Zero infrastructure imports in `domain/`

## Dependencies
#1, #2

## Reference
See `docs/project/MILESTONE-1.md` Issue #6
EOF
)" \
  "milestone-1,area:infra,complexity:M"

# Issue #7
create_issue \
  "feat(infra): PostgreSQL schema migrations" \
  "$(cat <<'EOF'
## Objective
Persistent operational storage with Alembic migrations.

## Description
SQLAlchemy 2.0 models, Alembic migrations, repository implementations for core entities.

## Acceptance criteria
- [ ] `make migrate` applies migrations against Docker PostgreSQL
- [ ] Integration test: insert/read Rider, Stage, RaceResult
- [ ] Foreign keys enforce ERD relationships

## Dependencies
#4, #6

## Reference
See `docs/project/MILESTONE-1.md` Issue #7
EOF
)" \
  "milestone-1,area:infra,complexity:M"

echo ""
echo "Done. Created 7 issues for Milestone 1."
echo "Next: create labels if missing — run scripts/create-github-labels.sh"
echo "Then: add issues to your GitHub Project board."
