"""SQLAlchemy ORM models for the plpipeline2627 database schema."""

import enum
from datetime import date as date_type

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# base

class Base(DeclarativeBase):
    pass


# enums

class Phase(str, enum.Enum):
    PRE_MATCH = "pre_match"
    CLOSING = "closing"


class Market(str, enum.Enum):
    MATCH_ODDS = "1x2"
    OVER_UNDER_2_5 = "over_under_2_5"
    ASIAN_HANDICAP = "asian_handicap"


class Selection(str, enum.Enum):
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"


# models

class Match(Base):
    __tablename__ = "match"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_code: Mapped[str] = mapped_column(String(4))
    competition: Mapped[str] = mapped_column(String(4))
    date: Mapped[date_type] = mapped_column(Date)
    time: Mapped[str | None] = mapped_column(String(5))
    home_team: Mapped[str] = mapped_column(String(64))
    away_team: Mapped[str] = mapped_column(String(64))

    fthg: Mapped[int]
    ftag: Mapped[int]
    ftr: Mapped[str] = mapped_column(String(1))

    hthg: Mapped[int | None]
    htag: Mapped[int | None]
    htr: Mapped[str | None] = mapped_column(String(1))

    referee: Mapped[str | None] = mapped_column(String(64))

    home_xg: Mapped[float | None] = mapped_column(Numeric(4, 2, asdecimal=False))
    away_xg: Mapped[float | None] = mapped_column(Numeric(4, 2, asdecimal=False))

    home_shots: Mapped[int | None]
    away_shots: Mapped[int | None]
    home_shots_on_target: Mapped[int | None]
    away_shots_on_target: Mapped[int | None]
    home_corners: Mapped[int | None]
    away_corners: Mapped[int | None]
    home_fouls: Mapped[int | None]
    away_fouls: Mapped[int | None]
    home_yellow_cards: Mapped[int | None]
    away_yellow_cards: Mapped[int | None]
    home_red_cards: Mapped[int | None]
    away_red_cards: Mapped[int | None]

    odds_quotes: Mapped[list[OddsQuote]] = relationship(back_populates="match")

    __table_args__ = (
        UniqueConstraint(
            "season_code",
            "date",
            "home_team",
            "away_team",
            name="uq_match_natural_key",
        ),
    )


class OddsQuote(Base):
    __tablename__ = "odds_quote"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match.id"))
    bookmaker: Mapped[str] = mapped_column(String(32))
    market: Mapped[Market] = mapped_column(String(20))
    phase: Mapped[Phase] = mapped_column(String(10))
    selection: Mapped[Selection] = mapped_column(String(10))
    line: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    price: Mapped[float] = mapped_column(Numeric(6, 2, asdecimal=False))

    match: Mapped[Match] = relationship(back_populates="odds_quotes")

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "bookmaker",
            "market",
            "phase",
            "selection",
            "line",
            name="uq_odds_natural_key",
            postgresql_nulls_not_distinct=True,
        ),
    )

class MatchStaging(Base):
    __tablename__ = "match_staging"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_code: Mapped[str] = mapped_column(String(4))
    competition: Mapped[str] = mapped_column(String(4))
    date: Mapped[date_type] = mapped_column(Date)
    time: Mapped[str | None] = mapped_column(String(5))
    home_team: Mapped[str] = mapped_column(String(64))
    away_team: Mapped[str] = mapped_column(String(64))

    fthg: Mapped[int | None]
    ftag: Mapped[int | None]
    ftr: Mapped[str | None] = mapped_column(String(1))

    hthg: Mapped[int | None]
    htag: Mapped[int | None]
    htr: Mapped[str | None] = mapped_column(String(1))

    referee: Mapped[str | None] = mapped_column(String(64))

    home_xg: Mapped[float | None] = mapped_column(Numeric(4, 2, asdecimal=False))
    away_xg: Mapped[float | None] = mapped_column(Numeric(4, 2, asdecimal=False))

    home_shots: Mapped[int | None]
    away_shots: Mapped[int | None]
    home_shots_on_target: Mapped[int | None]
    away_shots_on_target: Mapped[int | None]
    home_corners: Mapped[int | None]
    away_corners: Mapped[int | None]
    home_fouls: Mapped[int | None]
    away_fouls: Mapped[int | None]
    home_yellow_cards: Mapped[int | None]
    away_yellow_cards: Mapped[int | None]
    home_red_cards: Mapped[int | None]
    away_red_cards: Mapped[int | None]


class OddsQuoteStaging(Base):
    __tablename__ = "odds_quote_staging"

    id: Mapped[int] = mapped_column(primary_key=True)

    season_code: Mapped[str] = mapped_column(String(4))
    date: Mapped[date_type] = mapped_column(Date)
    home_team: Mapped[str] = mapped_column(String(64))
    away_team: Mapped[str] = mapped_column(String(64))

    bookmaker: Mapped[str | None] = mapped_column(String(32))
    market: Mapped[str | None] = mapped_column(String(20))
    phase: Mapped[str | None] = mapped_column(String(10))
    selection: Mapped[str | None] = mapped_column(String(10))
    line: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    price: Mapped[float | None] = mapped_column(Numeric(6, 2, asdecimal=False))