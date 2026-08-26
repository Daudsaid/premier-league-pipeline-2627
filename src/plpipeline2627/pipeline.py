from dataclasses import dataclass

from plpipeline2627.config import DEFAULT_SEASON, SeasonConfig
from plpipeline2627.db import get_session
from plpipeline2627.extract.fetch import fetch_csv
from plpipeline2627.extract.land import land_csv
from plpipeline2627.load.audit import AuditResult, audit_staging
from plpipeline2627.load.publish import publish
from plpipeline2627.load.staging import stage_matches, stage_odds_quotes
from plpipeline2627.transform.clean import clean_rows
from plpipeline2627.transform.parse import parse_csv


@dataclass
class PipelineResult:
    landed_path: str
    parsed_rows: int
    dead_letters: int
    audit: AuditResult
    published_matches: int
    published_odds_quotes: int


def run_etl(season: SeasonConfig = DEFAULT_SEASON) -> PipelineResult:
    content = fetch_csv(season)
    path = land_csv(content, season.season_code, season.competition)

    rows = parse_csv(content)
    clean_result = clean_rows(rows, season_code=season.season_code)

    session = get_session()
    try:
        stage_matches(session, clean_result.matches)
        stage_odds_quotes(session, clean_result.matches, clean_result.odds_quotes)
        session.commit()

        audit = audit_staging(session)

        published_matches = 0
        published_odds_quotes = 0

        if audit.passed:
            published_matches, published_odds_quotes = publish(session)
            session.commit()

        return PipelineResult(
            landed_path=str(path),
            parsed_rows=len(rows),
            dead_letters=len(clean_result.dead_letters),
            audit=audit,
            published_matches=published_matches,
            published_odds_quotes=published_odds_quotes,
        )
    finally:
        session.close()