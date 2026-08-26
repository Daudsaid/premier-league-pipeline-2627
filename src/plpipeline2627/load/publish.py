from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from plpipeline2627.models import (
    Match,
    MatchStaging,
    OddsQuote,
    OddsQuoteStaging,
)


def publish(session: Session) -> tuple[int, int]:
    staged_matches = session.scalars(select(MatchStaging)).all()

    match_rows = [
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
        for m in staged_matches
    ]

    if match_rows:
        stmt = insert(Match).values(match_rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_match_natural_key",
            set_={
                "fthg": stmt.excluded.fthg,
                "ftag": stmt.excluded.ftag,
                "ftr": stmt.excluded.ftr,
                "hthg": stmt.excluded.hthg,
                "htag": stmt.excluded.htag,
                "htr": stmt.excluded.htr,
                "referee": stmt.excluded.referee,
                "home_xg": stmt.excluded.home_xg,
                "away_xg": stmt.excluded.away_xg,
                "home_shots": stmt.excluded.home_shots,
                "away_shots": stmt.excluded.away_shots,
                "home_shots_on_target": stmt.excluded.home_shots_on_target,
                "away_shots_on_target": stmt.excluded.away_shots_on_target,
                "home_corners": stmt.excluded.home_corners,
                "away_corners": stmt.excluded.away_corners,
                "home_fouls": stmt.excluded.home_fouls,
                "away_fouls": stmt.excluded.away_fouls,
                "home_yellow_cards": stmt.excluded.home_yellow_cards,
                "away_yellow_cards": stmt.excluded.away_yellow_cards,
                "home_red_cards": stmt.excluded.home_red_cards,
                "away_red_cards": stmt.excluded.away_red_cards,
            },
        )
        session.execute(stmt)

    match_id_lookup: dict[tuple[str, object, str, str], int] = {
        row.season_code: None for row in []  # placeholder, replaced below
    }
    match_id_lookup = {}
    for row in session.scalars(select(Match)):
        key = (row.season_code, row.date, row.home_team, row.away_team)
        match_id_lookup[key] = row.id

    staged_odds = session.scalars(select(OddsQuoteStaging)).all()

    odds_rows = []
    for o in staged_odds:
        key = (o.season_code, o.date, o.home_team, o.away_team)
        match_id = match_id_lookup.get(key)
        if match_id is None:
            continue
        odds_rows.append(
            {
                "match_id": match_id,
                "bookmaker": o.bookmaker,
                "market": o.market,
                "phase": o.phase,
                "selection": o.selection,
                "line": o.line,
                "price": o.price,
            }
        )

    if odds_rows:
        chunk_size = 2000
        for i in range(0, len(odds_rows), chunk_size):
            chunk = odds_rows[i : i + chunk_size]
            stmt = insert(OddsQuote).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_odds_natural_key",
                set_={"price": stmt.excluded.price},
            )
            session.execute(stmt)

    session.execute(MatchStaging.__table__.delete())
    session.execute(OddsQuoteStaging.__table__.delete())

    return len(match_rows), len(odds_rows)