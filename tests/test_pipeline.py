"""Tests for plpipeline2627.pipeline: run_etl end to end."""

from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from plpipeline2627.config import DEFAULT_SEASON
from plpipeline2627.models import Match, OddsQuote
from plpipeline2627.pipeline import run_etl


@pytest.fixture()
def patched_pipeline(monkeypatch, engine, tmp_path):
    """Route run_etl()'s session at the test DB, and land CSVs under a throwaway dir."""
    TestSessionLocal = sessionmaker(bind=engine)
    monkeypatch.setattr("plpipeline2627.pipeline.get_session", TestSessionLocal)
    monkeypatch.setattr("plpipeline2627.extract.land.LANDED_DIR", tmp_path / "landed")


@respx.mock
def test_run_etl_end_to_end_returns_expected_counts(db_session, patched_pipeline, sample_csv_bytes):
    respx.get(DEFAULT_SEASON.source_url).mock(
        return_value=httpx.Response(200, content=sample_csv_bytes)
    )

    result = run_etl(DEFAULT_SEASON)

    assert result.parsed_rows == 10
    assert result.dead_letters == 0
    assert result.audit.passed is True
    assert result.published_matches == 10
    assert result.published_odds_quotes == 860


@respx.mock
def test_run_etl_lands_the_fetched_csv(db_session, patched_pipeline, sample_csv_bytes):
    respx.get(DEFAULT_SEASON.source_url).mock(
        return_value=httpx.Response(200, content=sample_csv_bytes)
    )

    result = run_etl(DEFAULT_SEASON)

    landed_path = Path(result.landed_path)
    assert landed_path.exists()
    assert landed_path.read_bytes() == sample_csv_bytes


@respx.mock
def test_run_etl_twice_is_idempotent(db_session, patched_pipeline, sample_csv_bytes):
    respx.get(DEFAULT_SEASON.source_url).mock(
        return_value=httpx.Response(200, content=sample_csv_bytes)
    )

    run_etl(DEFAULT_SEASON)
    second_result = run_etl(DEFAULT_SEASON)

    assert second_result.published_matches == 10
    assert second_result.published_odds_quotes == 860

    match_count = db_session.scalar(select(func.count()).select_from(Match))
    odds_count = db_session.scalar(select(func.count()).select_from(OddsQuote))
    assert match_count == 10
    assert odds_count == 860
