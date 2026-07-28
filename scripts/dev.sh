#!/usr/bin/env bash
# YellowMind local development helper
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

cmd="${1:-up}"

case "${cmd}" in
  up)
    docker compose up -d --build
    echo ""
    echo "YellowMind stack running:"
    echo "  API:     http://localhost:${API_PORT:-8000}/health"
    echo "  MLflow:  http://localhost:${MLFLOW_PORT:-5001}"
    echo "  Prefect: http://localhost:${PREFECT_PORT:-4200}"
    ;;
  down)
    docker compose down
    ;;
  logs)
    docker compose logs -f "${2:-}"
    ;;
  migrate)
    make migrate
    ;;
  *)
    echo "Usage: $0 {up|down|logs [service]|migrate}"
    exit 1
    ;;
esac
