from dataclasses import dataclass

from pydantic import ValidationError

from plpipeline2627.models import Match, OddsQuote
from plpipeline2627.transform.records import build_match, build_odds_quotes


@dataclass
class DeadLetter:
    row: dict[str, str]
    reason: str


@dataclass
class CleanResult:
    matches: list[Match]
    odds_quotes: list[list[OddsQuote]]
    dead_letters: list[DeadLetter]


def clean_rows(rows: list[dict[str, str]], season_code: str) -> CleanResult:
    matches: list[Match] = []
    odds_quotes: list[list[OddsQuote]] = []
    dead_letters: list[DeadLetter] = []

    for row in rows:
        try:
            match = build_match(row, season_code=season_code)
            quotes = build_odds_quotes(row)
        except ValidationError as e:
            dead_letters.append(DeadLetter(row=row, reason=str(e)))
            continue

        matches.append(match)
        odds_quotes.append(quotes)

    return CleanResult(matches=matches, odds_quotes=odds_quotes, dead_letters=dead_letters)

