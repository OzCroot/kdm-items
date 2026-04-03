"""
Re-parse all locally saved HTML pages through the updated scraper
and update the database. Uses the gear index (fetched fresh or cached)
to restore expansion/category metadata.
"""

import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path

import scraper

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
HTML_DIR = Path(os.environ.get("HTML_DIR", Path(__file__).parent / "html_pages"))
INDEX_CACHE = HTML_DIR / "_gear_index.html"
BASE_URL = "https://kingdomdeath.fandom.com"


def get_index_items() -> list[dict]:
    """Get gear index items, using cache if available."""
    if INDEX_CACHE.exists():
        print("Using cached gear index page.")
        html = INDEX_CACHE.read_text(encoding="utf-8")
    else:
        print("Fetching gear index page...")
        html = scraper.fetch_page(scraper.GEAR_INDEX_URL)
        INDEX_CACHE.write_text(html, encoding="utf-8")
    return scraper.parse_gear_index(html)


def main():
    print("=== Re-parsing local HTML pages ===\n")

    # Get index items for expansion/category metadata
    try:
        index_items = get_index_items()
        # Build lookup by URL
        meta_by_url = {}
        for item in index_items:
            meta_by_url[item["url"]] = item
        print(f"Index has {len(index_items)} items.\n")
    except Exception as e:
        print(f"Could not fetch index: {e}")
        print("Will use existing DB metadata.\n")
        meta_by_url = {}

    # Get all items from DB for URL mapping
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")
    rows = conn.execute("SELECT name, url, expansion, category FROM gear").fetchall()
    db_items = {r[0]: {"name": r[0], "url": r[1], "expansion": r[2], "category": r[3]} for r in rows}

    # Also build URL -> name mapping from DB
    url_to_name = {r[1]: r[0] for r in rows if r[1]}

    updated = 0
    html_files = sorted(HTML_DIR.glob("*.html"))
    html_files = [f for f in html_files if f.name != "_gear_index.html"]

    for filepath in html_files:
        html = filepath.read_text(encoding="utf-8")
        slug = filepath.stem

        # Try to find the matching item in DB or index
        possible_url = f"{BASE_URL}/wiki/{slug}"
        name = url_to_name.get(possible_url)
        if not name:
            # Try URL-decoded version
            for db_name, db_info in db_items.items():
                if db_info["url"] and slug in db_info["url"]:
                    name = db_name
                    break

        if not name:
            name = slug.replace("_", " ")

        # Get metadata: prefer index, fall back to DB
        meta = meta_by_url.get(possible_url, db_items.get(name, {"name": name, "url": possible_url}))

        # Parse the page
        gear_data = scraper.parse_gear_page(html, meta.get("name", name))

        # Insert/update
        scraper.insert_gear(conn, meta, gear_data)
        updated += 1

    conn.close()
    print(f"\nRe-parsed {updated} items from local HTML files.")

    # Stats
    conn = sqlite3.connect(str(DB_PATH))
    print("\n=== DATABASE SUMMARY ===")
    for label, query in [
        ("Total gear", "SELECT COUNT(*) FROM gear"),
        ("Weapons", "SELECT COUNT(*) FROM gear WHERE type='weapon'"),
        ("Armor", "SELECT COUNT(*) FROM gear WHERE type='armor'"),
        ("Items", "SELECT COUNT(*) FROM gear WHERE type='item'"),
        ("Other", "SELECT COUNT(*) FROM gear WHERE type='other'"),
        ("Unique keywords", "SELECT COUNT(DISTINCT keyword) FROM gear_keywords"),
        ("Crafting recipes", "SELECT COUNT(DISTINCT gear_id) FROM crafting_costs"),
    ]:
        result = conn.execute(query).fetchone()[0]
        print(f"  {label}: {result}")

    # Expansion breakdown
    print("\n=== BY EXPANSION ===")
    rows = conn.execute("SELECT expansion, COUNT(*) as c FROM gear GROUP BY expansion ORDER BY c DESC").fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    # Sample armor check
    print("\n=== SAMPLE ARMOR (verify hit_location/armor_rating) ===")
    rows = conn.execute("SELECT name, hit_location, armor_rating FROM gear WHERE type='armor' LIMIT 15").fetchall()
    for r in rows:
        print(f"  {r[0]}: Location={r[1]}, Armor={r[2]}")

    # Sample weapons
    print("\n=== SAMPLE WEAPONS ===")
    rows = conn.execute("SELECT name, speed, accuracy, strength FROM gear WHERE type='weapon' LIMIT 10").fetchall()
    for r in rows:
        print(f"  {r[0]}: Speed={r[1]}, Acc={r[2]}, Str={r[3]}")

    conn.close()


if __name__ == "__main__":
    main()
