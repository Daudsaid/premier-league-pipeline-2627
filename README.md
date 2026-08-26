# Premier League 2026/27 Data Pipeline

[![CI](https://github.com/Daudsaid/premier-league-pipeline-2627/actions/workflows/ci.yml/badge.svg)](https://github.com/Daudsaid/premier-league-pipeline-2627/actions/workflows/ci.yml)
[![Scheduled Run](https://github.com/Daudsaid/premier-league-pipeline-2627/actions/workflows/run-pipeline.yml/badge.svg)](https://github.com/Daudsaid/premier-league-pipeline-2627/actions/workflows/run-pipeline.yml)

A production-style batch ETL pipeline that fetches Premier League 2026/27
match results and multi-bookmaker betting odds, validates and transforms
them, and publishes them into Postgres — fully automated, running twice a
week without manual intervention for the length of the season.

Built as a second-season iteration of
[premier-league-pipeline](https://github.com/Daudsaid/premier-league-pipeline)
(2025/26), reusing that project's proven design while adapting to real
changes in the new season's source data.

## What it does

Every Monday and Thursday, a scheduled GitHub Actions workflow:

1. Fetches the live season CSV from football-data.co.uk
2. Validates and parses it — bad rows are dead-lettered, not allowed to
   break the run
3. Stages the data in Postgres, audits it, then publishes into production
   tables using natural-key upserts
4. Leaves the database in a consistent state whether the run succeeds,
   partially fails, or the source hasn't been updated yet

No step requires a person at a keyboard. The pipeline has run successfully
against real data locally, in CI, in Docker, and in production on a hosted
database — see [Verification](#verification) below.

## Architecture

```
football-data.co.uk (CSV)
        │
        ▼
   ┌─────────┐     ┌───────────┐     ┌──────────────────────┐
   │ Extract │ ──▶ │ Transform │ ──▶ │ Load (Write-Audit-Publish) │
   └─────────┘     └───────────┘     └──────────────────────┘
   fetch, land      parse, validate,   stage → audit → publish
   (BOM-aware,       build records,    (constraint-free staging,
   defensive         dead-letter        natural-key upserts into
   against an        invalid rows      production, all inside
   unpublished                          one transaction)
   source)
```

**Write-Audit-Publish**, not a direct insert: incoming data lands in
unconstrained staging tables first, gets audited (enum values, orphaned
rows, row counts) as real data sitting in Postgres — not just as Python
objects — and only a passing audit is allowed to merge into production.
A failed audit leaves the bad batch sitting in staging, inspectable,
rather than discarded or allowed to corrupt production.

**Idempotent by design.** Every table is keyed on a natural key (season +
date + teams for matches; match + bookmaker + market + phase + selection
+ line for odds, with `NULLS NOT DISTINCT` so markets without a handicap
line still dedupe correctly). Re-running the pipeline on the same or
updated source data updates existing rows in place — proven identical
locally, in CI, in Docker, and against production Neon data.

## Stack

Python 3.14 · PostgreSQL · SQLAlchemy 2.0 · Pydantic · Alembic · Typer ·
pandas · pytest + respx (all HTTP mocked — the test suite makes zero real
network calls)

## Project structure

```
src/plpipeline2627/
├── config.py          # season config, database URL (env-driven)
├── models.py          # SQLAlchemy schema: match, odds_quote + staging tables
├── db.py              # session factory
├── pipeline.py         # run_etl() — wires every stage together
├── cli.py              # `plp2627 run --season <code>`
├── extract/
│   ├── fetch.py        # HTTP fetch, BOM-aware, detects unpublished sources
│   └── land.py          # timestamped raw landing to disk
├── transform/
│   ├── parse.py         # CSV → dicts
│   ├── schema.py        # Pydantic validation (UK dates, result codes)
│   ├── records.py        # dicts → Match / OddsQuote ORM objects
│   └── clean.py           # dead-letter routing for invalid rows
└── load/
    ├── staging.py         # bulk insert into constraint-free staging
    ├── audit.py           # validates staged data before publish
    └── publish.py          # natural-key upsert into production, clears staging

alembic/                # schema migrations
tests/                  # 26 tests, fully respx-mocked
.github/workflows/
├── ci.yml               # lint + pytest against a Postgres service container
└── run-pipeline.yml      # Mon/Thu 8am UTC production run against Neon
```

## Local setup

```bash
git clone https://github.com/Daudsaid/premier-league-pipeline-2627.git
cd premier-league-pipeline-2627
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export PYTHONPATH=$PWD/src
```

**Known environment quirk (macOS, Python 3.14.5):** the editable install's
generated `.pth` file is created with the `UF_HIDDEN` flag set, which
Python's `site` module silently skips — so `import plpipeline2627` fails
without the `PYTHONPATH` export above, even though installation succeeds.
`chflags nohidden` does not reliably clear this on this build; setting
`PYTHONPATH` is the permanent workaround. Consider a shell alias:

```bash
alias plp2627_env='cd /path/to/premier-league-pipeline-2627 && source .venv/bin/activate && export PYTHONPATH=$PWD/src'
```

### Database

```bash
createdb -p 5432 plpipeline2627
alembic upgrade head
```

`DATABASE_URL` defaults to `postgresql+psycopg://localhost:5432/plpipeline2627`
if unset — point it elsewhere (e.g. a hosted instance) via environment
variable.

### Run it

```bash
plp2627 run --season 2627
```

Safe to re-run at any time — natural-key upserts mean existing rows are
updated, not duplicated.

## Testing

```bash
createdb -p 5432 plpipeline2627_test
pytest -v
```

26 tests across extract, transform, load, the full pipeline, and the CLI.
All HTTP is mocked with `respx` against a real committed CSV fixture — no
network access is required or performed.

## CI/CD

**`ci.yml`** runs on every push and pull request: `ruff check .` then the
full test suite against a real `postgres:18` service container in the
runner.

**`run-pipeline.yml`** runs the actual pipeline against production data on
a schedule (`0 8 * * 1,4` — Monday and Thursday, 8am UTC) and can also be
triggered manually via `workflow_dispatch`.

## Docker

```bash
docker compose up
```

Builds the pipeline image, starts Postgres with a healthcheck gating
startup order, runs `alembic upgrade head`, then runs the pipeline —
fully self-contained, verified idempotent across repeated runs against the
same volume.

## Production deployment

The scheduled workflow runs against a [Neon](https://neon.tech) Postgres
instance, configured via a `DATABASE_URL` repository secret. This keeps
production data persistent and reachable independent of any local
machine — the pipeline genuinely runs itself for the length of the
season, not just when someone happens to trigger it.

## Data model

Two production tables:

- **`match`** — one row per fixture: score, half-time score, referee,
  expected goals (`home_xg`/`away_xg`), and match stats (shots, corners,
  cards). Unique on `season_code, date, home_team, away_team`.
- **`odds_quote`** — one row per individual bookmaker price, normalized
  from the source's wide format (100+ columns) into `bookmaker`, `market`
  (1X2 / over-under 2.5 / Asian handicap), `phase` (pre-match / closing),
  `selection`, `line`, `price`. Unique on
  `match_id, bookmaker, market, phase, selection, line`, with
  `NULLS NOT DISTINCT` so 1X2/over-under rows (no handicap line) still
  dedupe correctly.

Plus two unconstrained staging tables (`match_staging`, `odds_quote_staging`)
used only during a load, and cleared automatically once a publish succeeds.

Bookmaker coverage genuinely varies by design, not by omission: B365, Max,
Avg, and BFE quote all three markets; BFD, BV, BW, PP, and SKB quote 1X2
only. This reflects the real source data, confirmed against a full
exploratory pass over a live sample rather than assumed.

## Known limitations

- **Venue is not modeled.** Not present in the source CSV. Three
  alternative sources were evaluated — a hand-maintained lookup table,
  football-data.org's API (venue exists but only on its per-match
  endpoint, at a cost of 380 individual calls a season against a 10
  requests/minute free tier), and the `openfootball/clubs` dataset (found,
  on inspection, to carry real staleness — its own documentation still
  listed a stadium a club left a decade ago). None met the bar this
  project holds itself to: every field should trace to something
  verifiably current in its source.
- **Odds are football-data.co.uk (free) only.** football-data.org gates
  odds behind a paid package even with a free API key.
- **No dimensional/star-schema layer yet.** A full Kimball-style design
  (dimension + fact tables) was scoped as a deliberate downstream
  analytical addition, not a replacement for the operational schema —
  documented separately, not yet implemented.

## Related

- [premier-league-pipeline](https://github.com/Daudsaid/premier-league-pipeline) —
  the 2025/26 season pipeline this project is built from