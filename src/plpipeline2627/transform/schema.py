from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MatchRow(BaseModel):
    div: str = Field(alias="Div")
    date: date_type = Field(alias="Date")
    time: str | None = Field(alias="Time", default=None)
    home_team: str = Field(alias="HomeTeam")
    away_team: str = Field(alias="AwayTeam")

    fthg: int = Field(alias="FTHG")
    ftag: int = Field(alias="FTAG")
    ftr: str = Field(alias="FTR")

    hthg: int | None = Field(alias="HTHG", default=None)
    htag: int | None = Field(alias="HTAG", default=None)
    htr: str | None = Field(alias="HTR", default=None)

    referee: str | None = Field(alias="Referee", default=None)

    home_xg: float | None = Field(alias="HxG", default=None)
    away_xg: float | None = Field(alias="AxG", default=None)

    home_shots: int | None = Field(alias="HS", default=None)
    away_shots: int | None = Field(alias="AS", default=None)
    home_shots_on_target: int | None = Field(alias="HST", default=None)
    away_shots_on_target: int | None = Field(alias="AST", default=None)
    home_corners: int | None = Field(alias="HC", default=None)
    away_corners: int | None = Field(alias="AC", default=None)
    home_fouls: int | None = Field(alias="HF", default=None)
    away_fouls: int | None = Field(alias="AF", default=None)
    home_yellow_cards: int | None = Field(alias="HY", default=None)
    away_yellow_cards: int | None = Field(alias="AY", default=None)
    home_red_cards: int | None = Field(alias="HR", default=None)
    away_red_cards: int | None = Field(alias="AR", default=None)

    model_config = {"populate_by_name": True}

    @field_validator("date", mode="before")
    @classmethod
    def parse_uk_date(cls, value: str) -> date_type:
        return datetime.strptime(value, "%d/%m/%Y").date()

    @field_validator("ftr", "htr")
    @classmethod
    def validate_result_code(cls, value: str | None) -> str | None:
        if value is not None and value not in ("H", "D", "A"):
            raise ValueError(f"invalid result code: {value!r}")
        return value