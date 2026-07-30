"""Make a stage unique within its edition.

Ingestion resolves a stage by `(edition, number)`, so the database should reject
a second row for the same slot rather than rely on the application getting it
right.

Revision ID: 003
Revises: 002
"""

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add the uniqueness constraint."""
    with op.batch_alter_table("stages") as batch:
        batch.create_unique_constraint("uq_stages_edition_number", ["tour_edition_id", "number"])


def downgrade() -> None:
    """Drop the uniqueness constraint."""
    with op.batch_alter_table("stages") as batch:
        batch.drop_constraint("uq_stages_edition_number", type_="unique")
