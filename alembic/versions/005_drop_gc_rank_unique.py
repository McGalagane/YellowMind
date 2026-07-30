"""Drop GC rank uniqueness that broke re-ingestion.

Standings are keyed by ``(stage, rider)``. Ranking is still unique in valid
data, but enforcing it in the database made re-ingest fail whenever two riders
swapped places: updating A to rank 2 while B still held rank 2 violated the
constraint mid-transaction.

Revision ID: 005
Revises: 004
"""

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Drop the rank uniqueness constraint."""
    with op.batch_alter_table("gc_standings") as batch:
        batch.drop_constraint("uq_gc_standings_stage_rank", type_="unique")


def downgrade() -> None:
    """Restore the rank uniqueness constraint."""
    with op.batch_alter_table("gc_standings") as batch:
        batch.create_unique_constraint("uq_gc_standings_stage_rank", ["stage_id", "rank"])
