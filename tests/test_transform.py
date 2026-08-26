"""Tests for plpipeline2627.transform: parse, records, clean."""

from datetime import date

from plpipeline2627.models import Market, Phase, Selection
from plpipeline2627.transform.clean import clean_rows
from plpipeline2627.transform.parse import parse_csv
from plpipeline2627.transform.records import build_match, build_odds_quotes

SEASON_CODE = "2627"


def test_parse_csv_returns_one_dict_per_data_row(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    assert len(rows) == 10


def test_parse_csv_strips_bom_from_first_column_name(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    assert "Div" in rows[0]


def test_build_match_maps_first_row_fields_correctly(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    match = build_match(rows[0], season_code=SEASON_CODE)

    assert match.season_code == SEASON_CODE
    assert match.competition == "E0"
    assert match.date == date(2026, 8, 21)
    assert match.home_team == "Arsenal"
    assert match.away_team == "Coventry"
    assert match.fthg == 3
    assert match.ftag == 0
    assert match.ftr == "H"
    assert match.home_xg == 1.88
    assert match.away_xg == 0.2


def test_build_odds_quotes_produces_86_quotes_for_first_row(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    quotes = build_odds_quotes(rows[0])

    # B365, Max, Avg, BFE have full coverage (1x2 + over/under + Asian handicap = 14 cols each);
    # BFD, BV, BW, PP, SKB have 1x2 only (6 cols each) -> 4*14 + 5*6 = 86
    assert len(quotes) == 86


def test_build_odds_quotes_includes_b365_home_pre_match_price(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    quotes = build_odds_quotes(rows[0])

    b365_home_pre_match = [
        q
        for q in quotes
        if q.bookmaker == "B365"
        and q.market == Market.MATCH_ODDS
        and q.phase == Phase.PRE_MATCH
        and q.selection == Selection.HOME
    ]
    assert len(b365_home_pre_match) == 1
    assert b365_home_pre_match[0].price == 1.2


def test_clean_rows_builds_a_match_and_quote_list_per_row(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    result = clean_rows(rows, season_code=SEASON_CODE)

    assert len(result.matches) == 10
    assert len(result.odds_quotes) == 10
    assert result.dead_letters == []


def test_clean_rows_total_odds_quotes_across_all_matches(sample_csv_bytes):
    rows = parse_csv(sample_csv_bytes)

    result = clean_rows(rows, season_code=SEASON_CODE)

    total_quotes = sum(len(quotes) for quotes in result.odds_quotes)
    assert total_quotes == 860


def test_clean_rows_sends_invalid_row_to_dead_letters():
    bad_row = {
        "Div": "E0",
        "Date": "21/08/2026",
        "HomeTeam": "Arsenal",
        "AwayTeam": "Coventry",
        "FTHG": "3",
        "FTAG": "0",
        "FTR": "Z",  # invalid result code
    }

    result = clean_rows([bad_row], season_code=SEASON_CODE)

    assert result.matches == []
    assert result.odds_quotes == []
    assert len(result.dead_letters) == 1
    assert result.dead_letters[0].row == bad_row
