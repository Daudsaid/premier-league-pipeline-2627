import typer

from plpipeline2627.config import DEFAULT_SEASON, SeasonConfig
from plpipeline2627.pipeline import run_etl

app = typer.Typer()


@app.callback()
def callback() -> None:
    pass


@app.command()
def run(season: str = typer.Option(DEFAULT_SEASON.season_code, help="Season code, e.g. 2627")) -> None:
    season_config = SeasonConfig(season_code=season)
    result = run_etl(season_config)

    typer.echo(f"Landed: {result.landed_path}")
    typer.echo(f"Parsed rows: {result.parsed_rows}")
    typer.echo(f"Dead letters: {result.dead_letters}")
    typer.echo(f"Audit passed: {result.audit.passed}")

    if not result.audit.passed:
        typer.echo(f"Audit issues: {result.audit.issues}")
        raise typer.Exit(code=1)

    typer.echo(f"Published: {result.published_matches} matches, {result.published_odds_quotes} odds quotes")


if __name__ == "__main__":
    app()