"""Stage 1: Fetch and parse the gear index page."""

import logging
import re
from html import unescape
from pathlib import Path

from config import BASE_URL, GEAR_INDEX_URL
from net import fetch
from utils import clean_html

log = logging.getLogger(__name__)


def fetch_gear_index(
    *, delay: float, max_retries: int, cache_dir: Path
) -> list[dict]:
    """Fetch the gear index page (or read from cache) and return parsed items.

    The raw HTML is cached at ``cache_dir/gear/_index.html`` so subsequent
    runs skip the network request.
    """
    cache_path = cache_dir / "gear" / "_index.html"

    if cache_path.exists():
        log.info("Reading cached gear index: %s", cache_path)
        html = cache_path.read_text(encoding="utf-8")
    else:
        log.info("Fetching gear index: %s", GEAR_INDEX_URL)
        html = fetch(GEAR_INDEX_URL, delay=delay, max_retries=max_retries)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html, encoding="utf-8")
        log.info("Cached gear index to %s", cache_path)

    items = parse_gear_index(html)
    log.info("Parsed %d gear items from index", len(items))
    return items


def parse_gear_index(html: str) -> list[dict]:
    """Parse the gear index HTML and return a list of gear item dicts.

    Each dict has keys: ``name``, ``url``, ``expansion``, ``category``.
    This is a pure parser with no I/O.
    """
    idx = html.find("mw-parser-output")
    if idx == -1:
        raise ValueError("Could not find content area in gear index page")
    content = html[idx:]

    list_idx = content.find('id="List_of_Gear"')
    if list_idx == -1:
        raise ValueError("Could not find 'List of Gear' section")
    content = content[list_idx:]

    items: list[dict] = []
    current_expansion = "Core Game"
    current_category = ""
    parts = re.split(r"(<h[234][^>]*>.*?</h[234]>)", content, flags=re.DOTALL)

    skip_pages = {
        "Gear", "Weapon", "Gear_Keyword", "Rare_Gear", "Pattern_Gear",
        "Starting_Gear", "Promo_Gear", "Gear_Special_Rule", "Affinities",
        "Gear_Keywords", "AI_Cards", "Hit_Location_Cards", "Activation",
        "Survival", "Damage", "Insane", "Attribute", "Affinity",
        "Affinity_Bonus", "Luck", "Hunt", "Showdown", "Cursed", "Death",
        "Hunt_Phase", "Irreplaceable", "Survivors", "Gear_Grid",
        "Story_Event", "Settlement_Event", "Hunt_Event", "Speed",
        "Accuracy", "Strength",
    }

    for part in parts:
        h_match = re.match(r"<(h[234])[^>]*>(.*?)</\1>", part, re.DOTALL)
        if h_match:
            level = h_match.group(1)
            heading_text = (
                clean_html(h_match.group(2)).replace("[]", "").strip()
            )
            if level == "h2":
                current_expansion = heading_text
                current_category = ""
            elif level == "h3":
                if "Expansion" in heading_text or heading_text in (
                    "Core Game",
                ):
                    current_expansion = heading_text
                    current_category = ""
                else:
                    current_category = heading_text
            elif level == "h4":
                current_category = heading_text
            continue

        links = re.findall(
            r'href="(/wiki/[^"#]+)"[^>]*title="([^"]+)"', part
        )
        for href, title in links:
            slug = href.split("/wiki/")[1] if "/wiki/" in href else ""
            if ":" in slug:
                continue
            if slug in skip_pages:
                continue
            if title in ("Bone", "Savage", "Frail"):
                continue
            items.append({
                "name": unescape(title),
                "url": f"{BASE_URL}{href}",
                "expansion": current_expansion,
                "category": current_category,
            })

    # Deduplicate by URL, preserving first occurrence.
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    return unique
