"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yellowmind.infrastructure.persistence.base import Base


class TourEditionModel(Base):
    """ORM model for Tour editions."""

    __tablename__ = "tour_editions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    teams: Mapped[list[TeamModel]] = relationship(back_populates="tour_edition")
    stages: Mapped[list[StageModel]] = relationship(back_populates="tour_edition")
    participations: Mapped[list[RiderParticipationModel]] = relationship(
        back_populates="tour_edition"
    )


class TeamModel(Base):
    """ORM model for teams, recorded once per edition."""

    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("tour_edition_id", "source_slug", name="uq_teams_edition_slug"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tour_edition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tour_editions.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(64), nullable=True)

    tour_edition: Mapped[TourEditionModel] = relationship(back_populates="teams")
    participations: Mapped[list[RiderParticipationModel]] = relationship(back_populates="team")


class RiderModel(Base):
    """ORM model for riders, independent of any edition."""

    __tablename__ = "riders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nationality: Mapped[str] = mapped_column(String(64), nullable=False)
    # Unique so ingestion can recognise a rider stored from an earlier edition.
    source_slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    participations: Mapped[list[RiderParticipationModel]] = relationship(back_populates="rider")
    results: Mapped[list[RaceResultModel]] = relationship(back_populates="rider")


class RiderParticipationModel(Base):
    """ORM model linking a rider to a team for one edition."""

    __tablename__ = "rider_participations"
    __table_args__ = (
        UniqueConstraint("tour_edition_id", "rider_id", name="uq_participation_edition_rider"),
        UniqueConstraint("tour_edition_id", "bib_number", name="uq_participation_edition_bib"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tour_edition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tour_editions.id"), nullable=False
    )
    rider_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("riders.id"), nullable=False)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=False)
    bib_number: Mapped[int] = mapped_column(Integer, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_gc_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Null together when the rider finished.
    abandonment_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    abandonment_stage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_young_rider: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tour_edition: Mapped[TourEditionModel] = relationship(back_populates="participations")
    rider: Mapped[RiderModel] = relationship(back_populates="participations")
    team: Mapped[TeamModel] = relationship(back_populates="participations")


class StageModel(Base):
    """ORM model for stages."""

    __tablename__ = "stages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tour_edition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tour_editions.id"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    stage_type: Mapped[str] = mapped_column(String(32), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    tour_edition: Mapped[TourEditionModel] = relationship(back_populates="stages")
    results: Mapped[list[RaceResultModel]] = relationship(back_populates="stage")


class RaceResultModel(Base):
    """ORM model for race results."""

    __tablename__ = "race_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    stage_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("stages.id"), nullable=False)
    rider_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("riders.id"), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    time_gap_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)

    stage: Mapped[StageModel] = relationship(back_populates="results")
    rider: Mapped[RiderModel] = relationship(back_populates="results")


class StageProfileModel(Base):
    """ORM model for stage profiles."""

    __tablename__ = "stage_profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    stage_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("stages.id"), unique=True, nullable=False
    )
    elevation_gain_m: Mapped[float] = mapped_column(Float, nullable=False)
    finish_type: Mapped[str] = mapped_column(String(16), nullable=False)
    profile_score: Mapped[int] = mapped_column(Integer, nullable=False)


class WeatherModel(Base):
    """ORM model for weather."""

    __tablename__ = "weather"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    stage_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("stages.id"), unique=True, nullable=False
    )
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=False)


class RiderRatingModel(Base):
    """ORM model for rider ratings."""

    __tablename__ = "rider_ratings"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    rider_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("riders.id"), nullable=False)
    stage_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("stages.id"), nullable=False)
    climbing: Mapped[float] = mapped_column(Float, nullable=False)
    sprint: Mapped[float] = mapped_column(Float, nullable=False)
    tt: Mapped[float] = mapped_column(Float, nullable=False)
    endurance: Mapped[float] = mapped_column(Float, nullable=False)
    recovery: Mapped[float] = mapped_column(Float, nullable=False)
    descending: Mapped[float] = mapped_column(Float, nullable=False)
    explosiveness: Mapped[float] = mapped_column(Float, nullable=False)
    form: Mapped[float] = mapped_column(Float, nullable=False)


class PredictionModel(Base):
    """ORM model for predictions."""

    __tablename__ = "predictions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tour_edition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tour_editions.id"), nullable=False
    )
    stage_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("stages.id"), nullable=True)
    target: Mapped[str] = mapped_column(String(64), nullable=False)
    probabilities: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SimulationModel(Base):
    """ORM model for simulations."""

    __tablename__ = "simulations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tour_edition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tour_editions.id"), nullable=False
    )
    n_iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    outcomes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TeamStrategyModel(Base):
    """ORM model for team strategies."""

    __tablename__ = "team_strategies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("teams.id"), unique=True, nullable=False)
    gc_leader_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("riders.id"), nullable=True)
    approach: Mapped[str] = mapped_column(String(255), nullable=False)
