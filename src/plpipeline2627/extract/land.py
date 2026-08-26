from datetime import UTC, datetime
from pathlib import Path

LANDED_DIR = Path("data/landed")


def land_csv(content: bytes, season_code: str, competition: str) -> Path:
    LANDED_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{competition}_{season_code}_{timestamp}.csv"
    path = LANDED_DIR / filename
    path.write_bytes(content)
    return path