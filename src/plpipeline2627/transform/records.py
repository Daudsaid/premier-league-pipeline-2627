from plpipeline2627.models import Market, Match, OddsQuote, Phase, Selection
from plpipeline2627.transform.schema import MatchRow

BOOKMAKER_MARKETS: dict[str, set[str]] = {
    "B365": {"1x2", "over_under", "asian_handicap"},
    "Max": {"1x2", "over_under", "asian_handicap"},
    "Avg": {"1x2", "over_under", "asian_handicap"},
    "BFE": {"1x2", "over_under", "asian_handicap"},
    "BFD": {"1x2"},
    "BV": {"1x2"},
    "BW": {"1x2"},
    "PP": {"1x2"},
    "SKB": {"1x2"},
}


def build_match(row: dict[str, str], season_code: str) -> Match:
    validated = MatchRow(**row)
    return Match(
        season_code=season_code,
        competition=validated.div,
        date=validated.date,
        time=validated.time,
        home_team=validated.home_team,
        away_team=validated.away_team,
        fthg=validated.fthg,
        ftag=validated.ftag,
        ftr=validated.ftr,
        hthg=validated.hthg,
        htag=validated.htag,
        htr=validated.htr,
        referee=validated.referee,
        home_xg=validated.home_xg,
        away_xg=validated.away_xg,
        home_shots=validated.home_shots,
        away_shots=validated.away_shots,
        home_shots_on_target=validated.home_shots_on_target,
        away_shots_on_target=validated.away_shots_on_target,
        home_corners=validated.home_corners,
        away_corners=validated.away_corners,
        home_fouls=validated.home_fouls,
        away_fouls=validated.away_fouls,
        home_yellow_cards=validated.home_yellow_cards,
        away_yellow_cards=validated.away_yellow_cards,
        home_red_cards=validated.home_red_cards,
        away_red_cards=validated.away_red_cards,
    )


def _price(row: dict[str, str], column: str) -> float | None:
    value = row.get(column, "").strip()
    return float(value) if value else None


def build_odds_quotes(row: dict[str, str]) -> list[OddsQuote]:
    quotes: list[OddsQuote] = []
    ah_line_pre = _price(row, "AHh")
    ah_line_close = _price(row, "AHCh")

    for bookmaker, markets in BOOKMAKER_MARKETS.items():
        if "1x2" in markets:
            for phase, prefix in [(Phase.PRE_MATCH, ""), (Phase.CLOSING, "C")]:
                for selection, suffix in [
                    (Selection.HOME, "H"),
                    (Selection.DRAW, "D"),
                    (Selection.AWAY, "A"),
                ]:
                    price = _price(row, f"{bookmaker}{prefix}{suffix}")
                    if price is not None:
                        quotes.append(
                            OddsQuote(
                                bookmaker=bookmaker,
                                market=Market.MATCH_ODDS,
                                phase=phase,
                                selection=selection,
                                line=None,
                                price=price,
                            )
                        )

        if "over_under" in markets:
            for phase, prefix in [(Phase.PRE_MATCH, ""), (Phase.CLOSING, "C")]:
                for selection, suffix in [
                    (Selection.OVER, f"{prefix}>2.5"),
                    (Selection.UNDER, f"{prefix}<2.5"),
                ]:
                    price = _price(row, f"{bookmaker}{suffix}")
                    if price is not None:
                        quotes.append(
                            OddsQuote(
                                bookmaker=bookmaker,
                                market=Market.OVER_UNDER_2_5,
                                phase=phase,
                                selection=selection,
                                line=None,
                                price=price,
                            )
                        )

        if "asian_handicap" in markets:
            for phase, prefix, line in [
                (Phase.PRE_MATCH, "", ah_line_pre),
                (Phase.CLOSING, "C", ah_line_close),
            ]:
                for selection, suffix in [
                    (Selection.HOME, "H"),
                    (Selection.AWAY, "A"),
                ]:
                    price = _price(row, f"{bookmaker}{prefix}AH{suffix}")
                    if price is not None:
                        quotes.append(
                            OddsQuote(
                                bookmaker=bookmaker,
                                market=Market.ASIAN_HANDICAP,
                                phase=phase,
                                selection=selection,
                                line=line,
                                price=price,
                            )
                        )

    return quotes