"""Stages 2-3: Download gear HTML pages and definition HTML pages to cache."""

import logging
import re
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path

from config import BASE_URL
from net import FetchError, fetch
from utils import slug_from_url

log = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Outcome summary for a batch download operation."""

    downloaded: int = 0
    skipped: int = 0
    failed: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 2 — gear pages
# ---------------------------------------------------------------------------


def download_gear_pages(
    items: list[dict],
    *,
    delay: float,
    max_retries: int,
    cache_dir: Path,
) -> DownloadResult:
    """Download each gear item's wiki page to cache.

    Pages are saved to ``cache_dir/gear/{slug}.html``.  If the file already
    exists the download is skipped.
    """
    result = DownloadResult()
    gear_dir = cache_dir / "gear"
    gear_dir.mkdir(parents=True, exist_ok=True)
    total = len(items)

    for i, item in enumerate(items, 1):
        slug = slug_from_url(item["url"])
        dest = gear_dir / f"{slug}.html"

        if dest.exists():
            result.skipped += 1
            continue

        try:
            html = fetch(item["url"], delay=delay, max_retries=max_retries)
            dest.write_text(html, encoding="utf-8")
            result.downloaded += 1
            log.info(
                "[%d/%d] Downloaded %s", i, total, item["name"]
            )
        except FetchError as exc:
            log.warning("Failed to download %s: %s", item["name"], exc)
            result.failed.append({"name": item["name"], "url": item["url"], "error": str(exc)})

    log.info(
        "Gear pages — downloaded: %d, skipped: %d, failed: %d",
        result.downloaded,
        result.skipped,
        len(result.failed),
    )
    return result


# ---------------------------------------------------------------------------
# Stage 3 — definition / category pages
# ---------------------------------------------------------------------------


def download_definition_pages(
    category_url: str,
    subdir: str,
    *,
    delay: float,
    max_retries: int,
    cache_dir: Path,
) -> list[dict]:
    """Fetch a wiki category page, then download every linked page.

    The category page itself is cached at
    ``cache_dir/definitions/{subdir}/_category.html``.  Individual pages are
    saved to ``cache_dir/definitions/{subdir}/{slug}.html``.

    Returns a list of ``{"title": str, "slug": str}`` for every page that
    is now present in the cache (whether freshly downloaded or already cached).
    """
    def_dir = cache_dir / "definitions" / subdir
    def_dir.mkdir(parents=True, exist_ok=True)

    # Fetch (or read) the category index page.
    cat_cache = def_dir / "_category.html"
    if cat_cache.exists():
        log.info("Reading cached category page: %s", cat_cache)
        cat_html = cat_cache.read_text(encoding="utf-8")
    else:
        log.info("Fetching category page: %s", category_url)
        cat_html = fetch(category_url, delay=delay, max_retries=max_retries)
        cat_cache.write_text(cat_html, encoding="utf-8")

    links = _get_category_links(cat_html)
    log.info("Found %d pages in category %s", len(links), subdir)

    cached_pages: list[dict] = []
    for i, link in enumerate(links, 1):
        slug = slug_from_url(link["url"])
        dest = def_dir / f"{slug}.html"

        if dest.exists():
            cached_pages.append({"title": link["title"], "slug": slug})
            continue

        try:
            html = fetch(link["url"], delay=delay, max_retries=max_retries)
            dest.write_text(html, encoding="utf-8")
            cached_pages.append({"title": link["title"], "slug": slug})
            log.info(
                "[%d/%d] Downloaded definition: %s", i, len(links), link["title"]
            )
        except FetchError as exc:
            log.warning("Failed to download %s: %s", link["title"], exc)

    return cached_pages


def _get_category_links(html: str) -> list[dict]:
    """Parse a wiki category page and extract member page links.

    Returns ``[{"title": str, "url": str}, ...]``.
    """
    idx = html.find("category-page__members")
    if idx == -1:
        return []

    section = html[idx : idx + 30000]
    raw_links = re.findall(
        r'href="(/wiki/[^"]+)"[^>]*title="([^"]+)"', section
    )

    seen: set[str] = set()
    links: list[dict] = []
    for href, title in raw_links:
        if href.startswith("/wiki/Category:"):
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append({"title": unescape(title), "url": f"{BASE_URL}{href}"})
    return links
