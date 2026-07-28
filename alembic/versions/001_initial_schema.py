"""Initial schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tour_editions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year"),
    )
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tour_edition_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("nationality", sa.String(length=3), nullable=False),
        sa.ForeignKeyConstraint(["tour_edition_id"], ["tour_editions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tour_edition_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("stage_type", sa.String(length=32), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["tour_edition_id"], ["tour_editions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "riders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("nationality", sa.String(length=3), nullable=False),
        sa.Column("pcs_slug", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "race_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("rider_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("time", sa.String(length=32), nullable=True),
        sa.Column("time_gap_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stage_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("elevation_gain_m", sa.Float(), nullable=False),
        sa.Column("finish_type", sa.String(length=16), nullable=False),
        sa.Column("profile_score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stage_id"),
    )
    op.create_table(
        "weather",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False),
        sa.Column("wind_speed_kmh", sa.Float(), nullable=False),
        sa.Column("precipitation_mm", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stage_id"),
    )
    op.create_table(
        "rider_ratings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rider_id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("climbing", sa.Float(), nullable=False),
        sa.Column("sprint", sa.Float(), nullable=False),
        sa.Column("tt", sa.Float(), nullable=False),
        sa.Column("endurance", sa.Float(), nullable=False),
        sa.Column("recovery", sa.Float(), nullable=False),
        sa.Column("descending", sa.Float(), nullable=False),
        sa.Column("explosiveness", sa.Float(), nullable=False),
        sa.Column("form", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tour_edition_id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=True),
        sa.Column("target", sa.String(length=64), nullable=False),
        sa.Column("probabilities", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"]),
        sa.ForeignKeyConstraint(["tour_edition_id"], ["tour_editions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "simulations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tour_edition_id", sa.Uuid(), nullable=False),
        sa.Column("n_iterations", sa.Integer(), nullable=False),
        sa.Column("outcomes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tour_edition_id"], ["tour_editions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "team_strategies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("gc_leader_id", sa.Uuid(), nullable=True),
        sa.Column("approach", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["gc_leader_id"], ["riders.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id"),
    )


def downgrade() -> None:
    op.drop_table("team_strategies")
    op.drop_table("simulations")
    op.drop_table("predictions")
    op.drop_table("rider_ratings")
    op.drop_table("weather")
    op.drop_table("stage_profiles")
    op.drop_table("race_results")
    op.drop_table("riders")
    op.drop_table("stages")
    op.drop_table("teams")
    op.drop_table("tour_editions")
