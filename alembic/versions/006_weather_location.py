"""Add provenance columns to weather.

Weather is sampled at a geocoded finish place. Storing the resolved name and
coordinates makes later audits possible when Open-Meteo and Wikipedia disagree
on a mountain top.

Revision ID: 006
Revises: 005
"""

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add location provenance to weather."""
    with op.batch_alter_table("weather") as batch:
        batch.add_column(sa.Column("location_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))

    # No weather rows exist yet in production backfills; tighten after add.
    op.execute("UPDATE weather SET location_name = '' WHERE location_name IS NULL")
    op.execute("UPDATE weather SET latitude = 0 WHERE latitude IS NULL")
    op.execute("UPDATE weather SET longitude = 0 WHERE longitude IS NULL")

    with op.batch_alter_table("weather") as batch:
        batch.alter_column("location_name", existing_type=sa.String(length=255), nullable=False)
        batch.alter_column("latitude", existing_type=sa.Float(), nullable=False)
        batch.alter_column("longitude", existing_type=sa.Float(), nullable=False)


def downgrade() -> None:
    """Drop location provenance from weather."""
    with op.batch_alter_table("weather") as batch:
        batch.drop_column("longitude")
        batch.drop_column("latitude")
        batch.drop_column("location_name")
