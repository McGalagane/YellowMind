"""Separate rider identity from edition participation.

Riders were bound to a team, and teams to an edition, so a rider appearing in
two editions needed two rows. This detaches rider identity from the edition and
moves the per-edition facts into `rider_participations`.

Nationality columns widen because the data source publishes country names such
as "United States" rather than three-letter codes.

Revision ID: 002
Revises: 001
"""

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Apply the participation model."""
    with op.batch_alter_table("teams") as batch:
        batch.add_column(sa.Column("source_slug", sa.String(255), nullable=False))
        batch.alter_column(
            "nationality",
            existing_type=sa.String(3),
            type_=sa.String(64),
            nullable=True,
        )
        batch.create_unique_constraint("uq_teams_edition_slug", ["tour_edition_id", "source_slug"])

    with op.batch_alter_table("riders") as batch:
        batch.alter_column("pcs_slug", new_column_name="source_slug")
        batch.alter_column(
            "nationality",
            existing_type=sa.String(3),
            type_=sa.String(64),
            nullable=False,
        )
        # The source publishes age per edition, never a birth date.
        batch.alter_column("birth_date", existing_type=sa.Date(), nullable=True)
        batch.create_unique_constraint("uq_riders_source_slug", ["source_slug"])
        batch.drop_column("team_id")

    op.create_table(
        "rider_participations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tour_edition_id",
            sa.Uuid(),
            sa.ForeignKey("tour_editions.id"),
            nullable=False,
        ),
        sa.Column("rider_id", sa.Uuid(), sa.ForeignKey("riders.id"), nullable=False),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("bib_number", sa.Integer(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("final_gc_position", sa.Integer(), nullable=True),
        sa.Column("abandonment_kind", sa.String(32), nullable=True),
        sa.Column("abandonment_stage", sa.Integer(), nullable=True),
        sa.Column("is_young_rider", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("tour_edition_id", "rider_id", name="uq_participation_edition_rider"),
        sa.UniqueConstraint("tour_edition_id", "bib_number", name="uq_participation_edition_bib"),
    )


def downgrade() -> None:
    """Revert to riders owning a team directly.

    Participation rows are dropped rather than folded back, since the old shape
    cannot represent a rider who took part in more than one edition.
    """
    op.drop_table("rider_participations")

    with op.batch_alter_table("riders") as batch:
        batch.drop_constraint("uq_riders_source_slug", type_="unique")
        batch.add_column(sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id"), nullable=True))
        batch.alter_column("birth_date", existing_type=sa.Date(), nullable=False)
        batch.alter_column(
            "nationality",
            existing_type=sa.String(64),
            type_=sa.String(3),
            nullable=False,
        )
        batch.alter_column("source_slug", new_column_name="pcs_slug")

    with op.batch_alter_table("teams") as batch:
        batch.drop_constraint("uq_teams_edition_slug", type_="unique")
        batch.alter_column(
            "nationality",
            existing_type=sa.String(64),
            type_=sa.String(3),
            nullable=False,
        )
        batch.drop_column("source_slug")
