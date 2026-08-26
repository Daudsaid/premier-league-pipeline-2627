"""Tests for plpipeline2627.extract: fetch, land."""

import httpx
import pytest
import respx

from plpipeline2627.config import SeasonConfig
from plpipeline2627.extract import land as land_module
from plpipeline2627.extract.fetch import SourceNotAvailableError, fetch_csv
from plpipeline2627.extract.land import land_csv

SEASON = SeasonConfig(season_code="2627")


@respx.mock
def test_fetch_csv_returns_content_unchanged_on_200(sample_csv_bytes):
    respx.get(SEASON.source_url).mock(return_value=httpx.Response(200, content=sample_csv_bytes))

    content = fetch_csv(SEASON)

    assert content == sample_csv_bytes


@respx.mock
def test_fetch_csv_raises_on_non_200_status():
    respx.get(SEASON.source_url).mock(return_value=httpx.Response(404))

    with pytest.raises(SourceNotAvailableError):
        fetch_csv(SEASON)


@respx.mock
def test_fetch_csv_raises_on_unexpected_body():
    # source not published yet: a 200 that isn't the CSV, e.g. an Apache "Multiple Choices" error page
    html_body = (
        b"<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">"
        b"<html><head><title>300 Multiple Choices</title></head>"
        b"<body><h1>Multiple Choices</h1></body></html>"
    )
    respx.get(SEASON.source_url).mock(return_value=httpx.Response(200, content=html_body))

    with pytest.raises(SourceNotAvailableError):
        fetch_csv(SEASON)


def test_land_csv_writes_expected_content_under_landed_dir(tmp_path, monkeypatch, sample_csv_bytes):
    monkeypatch.setattr(land_module, "LANDED_DIR", tmp_path / "landed")

    path = land_csv(sample_csv_bytes, season_code="2627", competition="E0")

    assert path.parent == tmp_path / "landed"
    assert path.read_bytes() == sample_csv_bytes


def test_land_csv_filenames_by_competition_and_season(tmp_path, monkeypatch, sample_csv_bytes):
    monkeypatch.setattr(land_module, "LANDED_DIR", tmp_path / "landed")

    path = land_csv(sample_csv_bytes, season_code="2627", competition="E0")

    assert path.name.startswith("E0_2627_")
    assert path.name.endswith(".csv")
