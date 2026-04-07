"""HTTP fetching with retry and rate limiting."""

import logging
import time
import urllib.request
import urllib.error
from pathlib import Path

from config import USER_AGENT

log = logging.getLogger(__name__)

RETRYABLE_CODES = {403, 429, 500, 502, 503, 504}


class FetchError(Exception):
    """Raised when a fetch fails after exhausting retries."""

    def __init__(self, url: str, status: int | None, message: str):
        self.url = url
        self.status = status
        super().__init__(f"HTTP {status}: {message} ({url})")


def fetch(url: str, *, delay: float = 1.0, max_retries: int = 3) -> str:
    """Fetch a URL and return decoded UTF-8 text.

    Sleeps `delay` seconds after each request. Retries on 403/429/5xx
    with exponential backoff (delay * 2^attempt, capped at 30s).
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read().decode("utf-8")
            time.sleep(delay)
            return result
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_CODES and attempt < max_retries:
                backoff = min(delay * (2 ** attempt), 30.0)
                log.warning("HTTP %d for %s — retrying in %.1fs", e.code, url, backoff)
                time.sleep(backoff)
                continue
            raise FetchError(url, e.code, e.reason) from e
        except urllib.error.URLError as e:
            if attempt < max_retries:
                backoff = min(delay * (2 ** attempt), 30.0)
                log.warning("URL error for %s — retrying in %.1fs: %s", url, backoff, e)
                time.sleep(backoff)
                continue
            raise FetchError(url, None, str(e.reason)) from e

    raise FetchError(url, None, "exhausted retries")


def download_binary(url: str, dest: Path, *, delay: float = 1.0, max_retries: int = 3) -> bool:
    """Fetch binary content and write to `dest`. Returns True on success."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            time.sleep(delay)
            return True
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_CODES and attempt < max_retries:
                backoff = min(delay * (2 ** attempt), 30.0)
                log.warning("HTTP %d downloading %s — retrying in %.1fs", e.code, url, backoff)
                time.sleep(backoff)
                continue
            log.warning("Failed to download %s: HTTP %d %s", url, e.code, e.reason)
            return False
        except Exception as e:
            if attempt < max_retries:
                backoff = min(delay * (2 ** attempt), 30.0)
                log.warning("Error downloading %s — retrying in %.1fs: %s", url, backoff, e)
                time.sleep(backoff)
                continue
            log.warning("Failed to download %s: %s", url, e)
            return False
