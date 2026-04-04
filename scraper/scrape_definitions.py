"""
Scrape keyword and special rule definitions from the KDM Fandom wiki.
Uses Category:Keywords and Category:Gear_Special_Rules as indexes.
"""

import os
import re
import time
import sqlite3
import urllib.request
from html import unescape
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://kingdomdeath.fandom.com"
REQUEST_DELAY = 1.0


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def clean_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    return text


def get_category_links(category_url: str) -> list[dict]:
    """Get all page links from a category page."""
    html = fetch_page(category_url)
    idx = html.find("category-page__members")
    if idx == -1:
        return []
    section = html[idx : idx + 30000]
    raw_links = re.findall(r'href="(/wiki/[^"]+)"[^>]*title="([^"]+)"', section)

    # Deduplicate and filter out sub-categories
    seen = set()
    links = []
    for href, title in raw_links:
        if href.startswith("/wiki/Category:"):
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append({"title": unescape(title), "url": f"{BASE_URL}{href}"})

    return links


def extract_definition(html: str) -> str:
    """Extract the definition text from a wiki page (first paragraphs before any heading)."""
    idx = html.find("mw-parser-output")
    if idx == -1:
        return ""
    content = html[idx : idx + 10000]

    # Cut at first h2 to only get the intro section
    first_h2 = content.find("<h2")
    if first_h2 > 0:
        content = content[:first_h2]

    # Extract paragraphs
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)
    text = "\n".join(clean_html(p) for p in paragraphs)
    text = text.strip()

    # Remove empty lines and excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def match_db_name(wiki_title: str, db_names: set[str]) -> str | None:
    """Try to match a wiki page title to a database keyword/rule name."""
    # Direct match
    if wiki_title in db_names:
        return wiki_title

    # Strip parenthetical disambiguation
    base = re.sub(r"\s*\([^)]+\)\s*$", "", wiki_title).strip()
    if base in db_names:
        return base

    # Handle "X" placeholders: "Block X" -> "Block 1", "Block 2", etc.
    if " X" in wiki_title or wiki_title.endswith(" X"):
        pattern = wiki_title.replace(" X", "")
        matches = [n for n in db_names if n.startswith(pattern)]
        if matches:
            return matches[0]  # Return first match; definition applies to all variants

    # Case-insensitive match
    lower_map = {n.lower(): n for n in db_names}
    if wiki_title.lower() in lower_map:
        return lower_map[wiki_title.lower()]
    if base.lower() in lower_map:
        return lower_map[base.lower()]

    return None


def scrape_definitions(category_url: str, db_names: set[str], label: str) -> dict[str, str]:
    """Scrape definitions from a wiki category and match to DB names."""
    print(f"\n=== Scraping {label} definitions ===")

    links = get_category_links(category_url)
    print(f"Found {len(links)} wiki pages")

    definitions: dict[str, str] = {}
    failed = []

    for i, link in enumerate(links, 1):
        title = link["title"]
        url = link["url"]

        # Find matching DB names (may match multiple for "X" patterns)
        matched = match_db_name(title, db_names)

        if not matched:
            # For X patterns, find ALL matching DB names
            base = title.replace(" X", "")
            x_matches = [n for n in db_names if n.startswith(base) and n != base]
            if not x_matches:
                print(f"  [{i}/{len(links)}] SKIP (no DB match): {title}")
                continue
        else:
            x_matches = []

        print(f"  [{i}/{len(links)}] Fetching: {title}...", end=" ", flush=True)

        try:
            html = fetch_page(url)
            definition = extract_definition(html)
            if definition:
                if x_matches:
                    for name in x_matches:
                        definitions[name] = definition
                    print(f"OK ({len(x_matches)} variants)")
                else:
                    definitions[matched] = definition
                    print("OK")
            else:
                print("EMPTY")
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append(title)

        time.sleep(REQUEST_DELAY)

    print(f"\nGot {len(definitions)} definitions, {len(failed)} failures")
    return definitions


def main():
    print(f"Database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    # Get existing keywords and rules from DB
    db_keywords = {r[0] for r in conn.execute("SELECT keyword FROM keyword_definitions").fetchall()}
    db_rules = {r[0] for r in conn.execute("SELECT rule FROM special_rule_definitions").fetchall()}
    db_locations = {r[0] for r in conn.execute("SELECT name FROM settlement_locations").fetchall()}
    print(f"DB has {len(db_keywords)} keywords, {len(db_rules)} special rules, {len(db_locations)} settlement locations")

    # Scrape keyword definitions
    kw_defs = scrape_definitions(
        f"{BASE_URL}/wiki/Category:Keywords",
        db_keywords,
        "Keyword",
    )

    # Scrape special rule definitions
    rule_defs = scrape_definitions(
        f"{BASE_URL}/wiki/Category:Gear_Special_Rules",
        db_rules,
        "Special Rule",
    )

    # Scrape settlement location definitions
    loc_defs = scrape_definitions(
        f"{BASE_URL}/wiki/Category:Settlement_Locations",
        db_locations,
        "Settlement Location",
    )

    # Update database
    print("\n=== Updating database ===")

    kw_updated = 0
    for keyword, definition in kw_defs.items():
        conn.execute(
            "INSERT OR REPLACE INTO keyword_definitions (keyword, definition) VALUES (?, ?)",
            (keyword, definition),
        )
        kw_updated += 1

    rule_updated = 0
    for rule, definition in rule_defs.items():
        conn.execute(
            "INSERT OR REPLACE INTO special_rule_definitions (rule, definition) VALUES (?, ?)",
            (rule, definition),
        )
        rule_updated += 1

    loc_updated = 0
    for name, definition in loc_defs.items():
        conn.execute(
            "INSERT OR REPLACE INTO settlement_locations (name, definition) VALUES (?, ?)",
            (name, definition),
        )
        loc_updated += 1

    conn.commit()
    conn.close()

    print(f"Updated {kw_updated} keyword definitions")
    print(f"Updated {rule_updated} special rule definitions")
    print(f"Updated {loc_updated} settlement location definitions")
    print("Done.")


if __name__ == "__main__":
    main()
