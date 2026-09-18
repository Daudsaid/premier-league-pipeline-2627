import time
from collections.abc import Callable

import httpx

from plpipeline2627.config import SeasonConfig

BOM = b"\xef\xbb\xbf"
USER_AGENT = "Mozilla/5.0 (compatible; plpipeline2627)"


class SourceNotAvailableError(Exception):
    pass


def _get_with_retries(
    url: str,
    retries: int = 3,
    backoff: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = httpx.get(
                url,
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            )
            # retry only on rate limiting or server errors
            if response.status_code != 429 and response.status_code < 500:
                return response
            last_error = SourceNotAvailableError(
                f"source returned status {response.status_code} for {url}"
            )
        except httpx.TransportError as exc:  # connection refused, timeouts, DNS, etc.
            last_error = exc

        if attempt < retries:
            sleep(backoff**attempt)  # 2s, then 4s

    raise SourceNotAvailableError(
        f"could not reach {url} after {retries} attempts: {last_error}"
    ) from last_error


def fetch_csv(season: SeasonConfig) -> bytes:
    response = _get_with_retries(season.source_url)

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
