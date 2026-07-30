"""Add GC standings and uniqueness for race results.

Stage results and GC standings are both resolved by ``(stage, rider)``, so the
database should reject a second row for the same pair.

Revision ID: 004
Revises: 003
"""

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create gc_standings and uniqueness on race_results."""
    with op.batch_alter_table("race_results") as batch:
        batch.create_unique_constraint("uq_race_results_stage_rider", ["stage_id", "rider_id"])

    op.create_table(
        "gc_standings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("stage_id", sa.Uuid(), sa.ForeignKey("stages.id"), nullable=False),
        sa.Column("rider_id", sa.Uuid(), sa.ForeignKey("riders.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("time", sa.String(32), nullable=True),
        sa.Column("time_gap_seconds", sa.Integer(), nullable=True),
        sa.UniqueConstraint("stage_id", "rider_id", name="uq_gc_standings_stage_rider"),
    )


def downgrade() -> None:
    """Drop gc_standings and the race_results uniqueness constraint."""
    op.drop_table("gc_standings")
    with op.batch_alter_table("race_results") as batch:
        batch.drop_constraint("uq_race_results_stage_rider", type_="unique")
