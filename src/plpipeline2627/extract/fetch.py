import httpx

from plpipeline2627.config import SeasonConfig

BOM = b"\xef\xbb\xbf"


class SourceNotAvailableError(Exception):
    pass


def fetch_csv(season: SeasonConfig) -> bytes:
    response = httpx.get(season.source_url, timeout=30.0)

    if response.status_code != 200:
        raise SourceNotAvailableError(
            f"source returned status {response.status_code} for {season.source_url}"
        )

    content = response.content
    content_check = content.removeprefix(BOM)

    if not content_check.startswith(b"Div,Date"):
        raise SourceNotAvailableError(
            f"unexpected content from {season.source_url}, source may not be published yet"
        )

    return content