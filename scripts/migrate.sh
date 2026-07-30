#!/usr/bin/env bash
# Run Alembic migrations against local PostgreSQL (Docker or native).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! command -v poetry >/dev/null 2>&1; then
  echo "Error: Poetry is required. Install from https://python-poetry.org/docs/#installation"
  exit 1
fi

if [[ ! -d "$(poetry env info -p 2>/dev/null || true)" ]]; then
  echo "Poetry environment not found — running poetry install..."
  poetry install --no-interaction
fi

poetry run python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" || {
  echo "Error: YellowMind requires Python 3.12+. Run: poetry env use python3.12 && poetry install"
  exit 1
}

export DATABASE_URL="${DATABASE_URL:-postgresql://yellowmind:yellowmind@localhost:5432/yellowmind}"

# Forward arguments so the script can run any Alembic command, e.g.
# `scripts/migrate.sh downgrade 001` or `scripts/migrate.sh current`.
# Without this, every invocation would upgrade regardless of what was asked.
ALEMBIC_ARGS=("$@")
if [[ ${#ALEMBIC_ARGS[@]} -eq 0 ]]; then
  ALEMBIC_ARGS=(upgrade head)
fi

echo "Running 'alembic ${ALEMBIC_ARGS[*]}' against ${DATABASE_URL}"
poetry run python -m alembic "${ALEMBIC_ARGS[@]}"
