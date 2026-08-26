"""Tests for plpipeline2627.cli: the `run` command."""

from datetime import date

import httpx
import pytest
import respx
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from plpipeline2627.cli import app
from plpipeline2627.config import DEFAULT_SEASON
from plpipeline2627.models import MatchStaging

runner = CliRunner()


@pytest.fixture()
def patched_pipeline(monkeypatch, engine, tmp_path):
    """Route run_etl()'s session at the test DB, and land CSVs under a throwaway dir."""
    TestSessionLocal = sessionmaker(bind=engine)
    monkeypatch.setattr("plpipeline2627.pipeline.get_session", TestSessionLocal)
    monkeypatch.setattr("plpipeline2627.extract.land.LANDED_DIR", tmp_path / "landed")


@respx.mock
def test_run_command_exits_0_and_prints_summary_on_success(
    db_session, patched_pipeline, sample_csv_bytes
):
    respx.get(DEFAULT_SEASON.source_url).mock(
        return_value=httpx.Response(200, content=sample_csv_bytes)
    )

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    assert "Parsed rows: 10" in result.output
    assert "Dead letters: 0" in result.output
    assert "Audit passed: True" in result.output
    assert "Published: 10 matches, 860 odds quotes" in result.output


@respx.mock
def test_run_command_exits_1_when_audit_fails(db_session, patched_pipeline, sample_csv_bytes):
    # pre-seed a row audit_staging will reject (null ftr), so run_etl's audit fails
    # regardless of what the mocked source returns
    db_session.execute(
        insert(MatchStaging),
        [
            {
                "season_code": "2627",
                "competition": "E0",
                "date": date(2026, 8, 21),
                "home_team": "Bad",
                "away_team": "Data",
                "ftr": None,
            }
        ],
    )
    db_session.commit()

    respx.get(DEFAULT_SEASON.source_url).mock(
        return_value=httpx.Response(200, content=sample_csv_bytes)
    )

    result = runner.invoke(app, ["run"])

    assert result.exit_code == 1
    assert "Audit passed: False" in result.output
    assert "Published" not in result.output
