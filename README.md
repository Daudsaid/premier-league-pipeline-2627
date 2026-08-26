# premier-league-pipeline-2627

Batch ETL pipeline for Premier League 2026/27 match and betting-odds data,
sourced from football-data.co.uk. Built as a second-season iteration of
[premier-league-pipeline](https://github.com/Daudsaid/premier-league-pipeline),
reusing the same proven architecture with adjustments for this season's
source-format changes (expected goals columns, a revised bookmaker roster).

## Architecture

Extract → Transform → Load, following the
[Write-Audit-Publish](https://www.getdbt.com/blog/write-audit-publish) pattern:

- **Extract** (`extract/`) — fetches the live CSV, defensively checks for
  "not yet published" responses, lands raw bytes to disk with a timestamp.
- **Transform** (`transform/`) — parses CSV (BOM-aware), validates and types
  each row via Pydantic, builds ORM objects, routes invalid rows to a
  dead-letter list rather than failing the whole batch.
- **Load** (`load/`) — stages data in constraint-free tables, audits the
  staged batch (enum values, orphaned rows), then publishes into production
  via natural-key upserts inside one transaction. Staging is cleared only on
  a successful publish.

## Stack

Python 3.14, PostgreSQL, SQLAlchemy 2.0, Pydantic, Alembic, Typer, pandas,
pytest + respx (all HTTP mocked in tests — no network required to run the
suite).

## Setup

```bash
git clone <this-repo>
cd premier-league-pipeline-2627
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export PYTHONPATH=$PWD/src
```

**Known environment quirk (macOS, Python 3.14.5):** the editable install's
generated `.pth` file is created with the `UF_HIDDEN` flag set, which
Python's `site` module silently skips — so `import plpipeline2627` fails
without the `PYTHONPATH` export above, even though the install itself
succeeded. `chflags nohidden` does not reliably clear this on this build.
Setting `PYTHONPATH` is the permanent workaround; consider a shell alias:

```bash
alias plp2627_env='cd /path/to/premier-league-pipeline-2627 && source .venv/bin/activate && export PYTHONPATH=$PWD/src'
```

## Database

```bash
createdb -p 5432 plpipeline2627
alembic upgrade head
```

Set `DATABASE_URL` to point elsewhere (e.g. a hosted Postgres instance);
defaults to `postgresql+psycopg://localhost:5432/plpipeline2627` if unset.

## Usage

```bash
plp2627 run --season 2627
```

Fetches the live season file, parses, validates, and publishes into
Postgres. Safe to re-run — natural-key upserts mean existing rows are
updated in place, not duplicated.

## Testing

```bash
createdb -p 5432 plpipeline2627_test
pytest -v
```

All HTTP calls are mocked via `respx`; no real network access is required
or performed during the test suite.

## Data model

Two production tables (`match`, `odds_quote`) plus two unconstrained
staging tables used only during a load. `match` is keyed naturally on
season + date + both teams; `odds_quote` on match + bookmaker + market +
phase + selection + line, with `NULLS NOT DISTINCT` so 1X2/over-under rows
(which have no handicap line) still dedupe correctly against reruns.

## Known limitations

- **Venue is not modeled.** Not present in the source CSV; the alternative
  sources checked (a hand-maintained lookup, football-data.org's paid-tier
  venue field, the openfootball/clubs dataset) all carried real staleness
  or cost risk inconsistent with this project's principle that every field
  traces to something verifiably current in its source.
- **Odds are free-tier football-data.co.uk data only** — no live in-play
  odds, no odds from football-data.org (which gates odds behind a paid
  package even with a free API key).