# gives access to environment variables via os.environ
import os

# decorator that auto-generates __init__, __repr__, __eq__ from type-annotated attributes
from dataclasses import dataclass


# frozen=True makes instances immutable — can't reassign fields after creation
@dataclass(frozen=True)
class SeasonConfig:
    # e.g. "2627" — required field, no default, must be passed in
    season_code: str

    # defaults to Premier League's code if not specified
    competition: str = "E0"

    # lets source_url be accessed as an attribute (config.source_url), not called as a method
    @property
    def source_url(self) -> str:
        # f-string interpolates self.season_code and self.competition directly into the URL
        return f"https://www.football-data.co.uk/mmz4281/{self.season_code}/{self.competition}.csv"


# this season's config, created once at module-import time
DEFAULT_SEASON = SeasonConfig(
    season_code="2627",
)

DATABASE_URL = os.environ.get(
    # look for this env var first (this is what GitHub Actions/Neon will set later)
    "DATABASE_URL",
    # fallback used when the env var isn't set (local dev)
    "postgresql+psycopg://localhost:5432/plpipeline2627",
)