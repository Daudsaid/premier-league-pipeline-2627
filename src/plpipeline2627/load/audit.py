from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plpipeline2627.models import Market, MatchStaging, OddsQuoteStaging, Phase, Selection


@dataclass
class AuditResult:
    match_count: int
    odds_quote_count: int
    issues: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0


def audit_staging(session: Session) -> AuditResult:
    issues: list[str] = []

    match_count = session.scalar(select(func.count()).select_from(MatchStaging))
    odds_quote_count = session.scalar(select(func.count()).select_from(OddsQuoteStaging))

    null_ftr = session.scalar(
        select(func.count()).select_from(MatchStaging).where(MatchStaging.ftr.is_(None))
    )
    if null_ftr:
        issues.append(f"{null_ftr} match_staging rows have null ftr")

    valid_markets = {m.value for m in Market}
    bad_markets = session.scalars(
        select(OddsQuoteStaging.market)
        .distinct()
        .where(OddsQuoteStaging.market.notin_(valid_markets))
    ).all()
    if bad_markets:
        issues.append(f"unrecognized market values: {bad_markets}")

    valid_phases = {p.value for p in Phase}
    bad_phases = session.scalars(
        select(OddsQuoteStaging.phase)
        .distinct()
        .where(OddsQuoteStaging.phase.notin_(valid_phases))
    ).all()
    if bad_phases:
        issues.append(f"unrecognized phase values: {bad_phases}")

    valid_selections = {s.value for s in Selection}
    bad_selections = session.scalars(
        select(OddsQuoteStaging.selection)
        .distinct()
        .where(OddsQuoteStaging.selection.notin_(valid_selections))
    ).all()
    if bad_selections:
        issues.append(f"unrecognized selection values: {bad_selections}")

    orphaned = session.scalar(
        select(func.count())
        .select_from(OddsQuoteStaging)
        .outerjoin(
            MatchStaging,
            (OddsQuoteStaging.season_code == MatchStaging.season_code)
            & (OddsQuoteStaging.date == MatchStaging.date)
            & (OddsQuoteStaging.home_team == MatchStaging.home_team)
            & (OddsQuoteStaging.away_team == MatchStaging.away_team),
        )
        .where(MatchStaging.id.is_(None))
    )
    if orphaned:
        issues.append(f"{orphaned} odds_quote_staging rows have no matching match_staging row")

    return AuditResult(
        match_count=match_count or 0,
        odds_quote_count=odds_quote_count or 0,
        issues=issues,
    )