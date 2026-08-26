from sqlalchemy import insert
from sqlalchemy.orm import Session

from plpipeline2627.models import Match, MatchStaging, OddsQuote, OddsQuoteStaging


def stage_matches(session: Session, matches: list[Match]) -> None:
    rows = [
        {
            "season_code": m.season_code,
            "competition": m.competition,
            "date": m.date,
            "time": m.time,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "fthg": m.fthg,
            "ftag": m.ftag,
            "ftr": m.ftr,
            "hthg": m.hthg,
            "htag": m.htag,
            "htr": m.htr,
            "referee": m.referee,
            "home_xg": m.home_xg,
            "away_xg": m.away_xg,
            "home_shots": m.home_shots,
            "away_shots": m.away_shots,
            "home_shots_on_target": m.home_shots_on_target,
            "away_shots_on_target": m.away_shots_on_target,
            "home_corners": m.home_corners,
            "away_corners": m.away_corners,
            "home_fouls": m.home_fouls,
            "away_fouls": m.away_fouls,
            "home_yellow_cards": m.home_yellow_cards,
            "away_yellow_cards": m.away_yellow_cards,
            "home_red_cards": m.home_red_cards,
            "away_red_cards": m.away_red_cards,
        }
        for m in matches
    ]
    if rows:
        session.execute(insert(MatchStaging), rows)


def stage_odds_quotes(
    session: Session,
    matches: list[Match],
    odds_quotes: list[list[OddsQuote]],
) -> None:
    rows = []
    for match, quotes in zip(matches, odds_quotes):
        for q in quotes:
            rows.append(
                {
                    "season_code": match.season_code,
                    "date": match.date,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "bookmaker": q.bookmaker,
                    "market": q.market,
                    "phase": q.phase,
                    "selection": q.selection,
                    "line": q.line,
                    "price": q.price,
                }
            )
    if rows:
        session.execute(insert(OddsQuoteStaging), rows)