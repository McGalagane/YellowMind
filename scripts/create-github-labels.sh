#!/usr/bin/env bash
# Create standard YellowMind GitHub labels.
# Prerequisites: gh auth login
set -euo pipefail

REPO="${GITHUB_REPO:-McGalagane/YellowMind}"

create_label() {
  local name="$1"
  local color="$2"
  local description="$3"
  gh label create "${name}" --repo "${REPO}" --color "${color}" --description "${description}" --force 2>/dev/null || \
    gh label edit "${name}" --repo "${REPO}" --color "${color}" --description "${description}" 2>/dev/null || true
}

echo "Creating labels on ${REPO}..."

for i in $(seq 1 10); do
  create_label "milestone-${i}" "0E8A16" "Milestone ${i}"
done

create_label "area:infra" "1D76DB" "Infrastructure and tooling"
create_label "area:data" "FBCA04" "Data ingestion and storage"
create_label "area:features" "D4C5F9" "Feature engineering"
create_label "area:model" "B60205" "Machine learning models"
create_label "area:simulation" "5319E7" "Monte Carlo simulation"
create_label "area:api" "006B75" "REST API"
create_label "area:frontend" "E99695" "Next.js dashboard"
create_label "area:docs" "0075CA" "Documentation"

create_label "complexity:XS" "C5DEF5" "Extra small — hours"
create_label "complexity:S" "C5DEF5" "Small — half day"
create_label "complexity:M" "C5DEF5" "Medium — 1-2 days"
create_label "complexity:L" "C5DEF5" "Large — 3-5 days"
create_label "complexity:XL" "C5DEF5" "Extra large — 1+ week"

echo "Labels ready."
