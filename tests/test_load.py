"""Tests for plpipeline2627.load: staging, audit, publish."""

from datetime import date

from sqlalchemy import func, insert, select

from plpipeline2627.load.audit import audit_staging
from plpipeline2627.load.publish import publish
from plpipeline2627.load.staging import stage_matches, stage_odds_quotes
from plpipeline2627.models import Match, MatchStaging, OddsQuote, OddsQuoteStaging
from plpipeline2627.transform.clean import clean_rows
from plpipeline2627.transform.parse import parse_csv

SEASON_CODE = "2627"


def _stage_sample(session, sample_csv_bytes):
    """Parse, clean, and stage the sample fixture; returns the CleanResult used."""
    rows = parse_csv(sample_csv_bytes)
    clean_result = clean_rows(rows, season_code=SEASON_CODE)
    stage_matches(session, clean_result.matches)
    stage_odds_quotes(session, clean_result.matches, clean_result.odds_quotes)
    session.commit()
    return clean_result


def test_stage_matches_inserts_expected_row_count(db_session, sample_csv_bytes):
    _stage_sample(db_session, sample_csv_bytes)

    match_count = db_session.scalar(select(func.count()).select_from(MatchStaging))

    assert match_count == 10


def test_stage_odds_quotes_inserts_expected_row_count(db_session, sample_csv_bytes):
    _stage_sample(db_session, sample_csv_bytes)

    odds_count = db_session.scalar(select(func.count()).select_from(OddsQuoteStaging))

    assert odds_count == 860


def test_audit_staging_passes_on_clean_staged_data(db_session, sample_csv_bytes):
    _stage_sample(db_session, sample_csv_bytes)

    audit = audit_staging(db_session)

    assert audit.passed is True
    assert audit.issues == []
    assert audit.match_count == 10
    assert audit.odds_quote_count == 860


def test_audit_staging_catches_invalid_market_value(db_session):
    db_session.execute(
        insert(MatchStaging),
        [
            {
                "season_code": SEASON_CODE,
                "competition": "E0",
                "date": date(2026, 8, 21),
                "home_team": "Arsenal",
                "away_team": "Coventry",
                "ftr": "H",
            }
        ],
    )
    db_session.execute(
        insert(OddsQuoteStaging),
        [
            {
                "season_code": SEASON_CODE,
                "date": date(2026, 8, 21),
                "home_team": "Arsenal",
                "away_team": "Coventry",
                "bookmaker": "B365",
                "market": "not_a_real_market",
                "phase": "pre_match",
                "selection": "home",
                "price": 1.5,
            }
        ],
    )
    db_session.commit()

    audit = audit_staging(db_session)

    assert audit.passed is False
    assert any("not_a_real_market" in issue for issue in audit.issues)


def test_audit_staging_catches_orphaned_odds_quote(db_session):
    # no matching match_staging row for this natural key
    db_session.execute(
        insert(OddsQuoteStaging),
        [
            {
                "season_code": SEASON_CODE,
                "date": date(2026, 8, 21),
                "home_team": "Nonexistent",
                "away_team": "Team",
                "bookmaker": "B365",
                "market": "1x2",
                "phase": "pre_match",
                "selection": "home",
                "price": 1.5,
            }
        ],
    )
    db_session.commit()

    audit = audit_staging(db_session)

    assert audit.passed is False
    assert any("no matching match_staging row" in issue for issue in audit.issues)


def test_publish_moves_staged_data_into_production_tables(db_session, sample_csv_bytes):
    _stage_sample(db_session, sample_csv_bytes)

    published_matches, published_odds_quotes = publish(db_session)
    db_session.commit()

    assert published_matches == 10
    assert published_odds_quotes == 860

    match_count = db_session.scalar(select(func.count()).select_from(Match))
    odds_count = db_session.scalar(select(func.count()).select_from(OddsQuote))
    assert match_count == 10
    assert odds_count == 860


def test_publish_empties_staging_tables_afterward(db_session, sample_csv_bytes):
    _stage_sample(db_session, sample_csv_bytes)

    publish(db_session)
    db_session.commit()

    match_staging_count = db_session.scalar(select(func.count()).select_from(MatchStaging))
    odds_staging_count = db_session.scalar(select(func.count()).select_from(OddsQuoteStaging))
    assert match_staging_count == 0
    assert odds_staging_count == 0


def test_publish_is_idempotent_when_run_twice(db_session, sample_csv_bytes):
    clean_result = _stage_sample(db_session, sample_csv_bytes)
    publish(db_session)
    db_session.commit()

    # simulate re-running the pipeline against the same source data
    stage_matches(db_session, clean_result.matches)
    stage_odds_quotes(db_session, clean_result.matches, clean_result.odds_quotes)
    db_session.commit()
    publish(db_session)
    db_session.commit()

    match_count = db_session.scalar(select(func.count()).select_from(Match))
    odds_count = db_session.scalar(select(func.count()).select_from(OddsQuote))
    assert match_count == 10
    assert odds_count == 860
