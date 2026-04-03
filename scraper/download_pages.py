"""
Download all gear pages as local HTML files for offline reference.
Also retries any items still missing from the database.
"""

import os
import re
import time
import json
import sqlite3
import urllib.request
from html import unescape
from pathlib import Path

BASE_URL = "https://kingdomdeath.fandom.com"
GEAR_INDEX_URL = f"{BASE_URL}/wiki/Gear"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
HTML_DIR = Path(os.environ.get("HTML_DIR", Path(__file__).parent / "html_pages"))
REQUEST_DELAY = 1.5  # longer delay to avoid 403s


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def slug_from_url(url: str) -> str:
    """Convert URL to safe filename."""
    slug = url.split("/wiki/")[-1]
    # Make filesystem-safe
    slug = slug.replace("%27", "'").replace("%26", "&").replace("%28", "(").replace("%29", ")")
    slug = re.sub(r'[<>:"/\\|?*]', '_', slug)
    return slug


def get_all_gear_urls_from_db() -> list[dict]:
    """Get all gear items from the database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT name, url FROM gear").fetchall()
    conn.close()
    return [{"name": r["name"], "url": r["url"]} for r in rows]


FAILED_ITEMS = [
    {"name": "Lantern Greaves", "url": f"{BASE_URL}/wiki/Lantern_Greaves"},
    {"name": "Lion Skin Cloak", "url": f"{BASE_URL}/wiki/Lion_Skin_Cloak"},
    {"name": "Arc Bow", "url": f"{BASE_URL}/wiki/Arc_Bow"},
    {"name": "Phoenix Greaves", "url": f"{BASE_URL}/wiki/Phoenix_Greaves"},
    {"name": "Rawhide Vest", "url": f"{BASE_URL}/wiki/Rawhide_Vest"},
    {"name": "Beast Knuckle", "url": f"{BASE_URL}/wiki/Beast_Knuckle"},
    {"name": "Elder Earrings", "url": f"{BASE_URL}/wiki/Elder_Earrings"},
    {"name": "Screaming Leg Warmers", "url": f"{BASE_URL}/wiki/Screaming_Leg_Warmers"},
    {"name": "Talon Knife", "url": f"{BASE_URL}/wiki/Talon_Knife"},
    {"name": "Digging Claws", "url": f"{BASE_URL}/wiki/Digging_Claws"},
    {"name": "Gorment Suit", "url": f"{BASE_URL}/wiki/Gorment_Suit"},
    {"name": "Greater Gaxe", "url": f"{BASE_URL}/wiki/Greater_Gaxe"},
    {"name": "Lion God Statue", "url": f"{BASE_URL}/wiki/Lion_God_Statue"},
    {"name": "Gloom Hammer", "url": f"{BASE_URL}/wiki/Gloom_Hammer"},
    {"name": "Gloom Mehndi", "url": f"{BASE_URL}/wiki/Gloom_Mehndi"},
    {"name": "Body Suit", "url": f"{BASE_URL}/wiki/Body_Suit"},
    {"name": "Hooded Scrap Katar", "url": f"{BASE_URL}/wiki/Hooded_Scrap_Katar"},
    {"name": "Bloodglass Katar", "url": f"{BASE_URL}/wiki/Bloodglass_Katar"},
    {"name": "Bloodglass Saw", "url": f"{BASE_URL}/wiki/Bloodglass_Saw"},
    {"name": "Crimson Bow", "url": f"{BASE_URL}/wiki/Crimson_Bow"},
    {"name": "Aya's Sword", "url": f"{BASE_URL}/wiki/Aya%27s_Sword"},
    {"name": "Cloth Leggings", "url": f"{BASE_URL}/wiki/Cloth_Leggings"},
    {"name": "Tabard", "url": f"{BASE_URL}/wiki/Tabard"},
    {"name": "Hope Stealer", "url": f"{BASE_URL}/wiki/Hope_Stealer"},
    {"name": "Lantern Brassiere", "url": f"{BASE_URL}/wiki/Lantern_Brassiere"},
    {"name": "Speaker Cult Knife", "url": f"{BASE_URL}/wiki/Speaker_Cult_Knife"},
    {"name": "Ashen Shears", "url": f"{BASE_URL}/wiki/Ashen_Shears"},
    {"name": "Refined Lantern Axe", "url": f"{BASE_URL}/wiki/Refined_Lantern_Axe"},
    {"name": "Ghost Garters - Legs (Gear)", "url": f"{BASE_URL}/wiki/Ghost_Garters_-_Legs_(Gear)"},
    {"name": "Gold Cat Costume (Gear)", "url": f"{BASE_URL}/wiki/Gold_Cat_Costume_(Gear)"},
    {"name": "Plated Shield (Gear)", "url": f"{BASE_URL}/wiki/Plated_Shield_(Gear)"},
    {"name": "Prismatic Lantern", "url": f"{BASE_URL}/wiki/Prismatic_Lantern"},
]


def main():
    HTML_DIR.mkdir(exist_ok=True)

    print("=== Downloading Gear Pages Locally ===\n")

    # Get items from DB + failed items list
    db_items = get_all_gear_urls_from_db()
    # Merge: DB items + failed items not in DB
    db_urls = {i["url"] for i in db_items}
    items = db_items + [i for i in FAILED_ITEMS if i["url"] not in db_urls]
    print(f"Found {len(items)} items ({len(db_items)} in DB + {len(items) - len(db_items)} missing).\n")

    # Check which HTML files we already have
    existing_files = {f.stem for f in HTML_DIR.glob("*.html")}

    # Download all pages
    total = len(items)
    downloaded = 0
    skipped = 0
    failed = []

    for i, item in enumerate(items, 1):
        name = item["name"]
        url = item["url"]
        slug = slug_from_url(url)
        filepath = HTML_DIR / f"{slug}.html"

        pct = i * 100 // total
        if slug in existing_files:
            skipped += 1
            print(f"[{i}/{total}] ({pct}%) SKIP (cached): {name}")
            continue

        print(f"[{i}/{total}] ({pct}%) Downloading: {name}...", end=" ", flush=True)

        try:
            html = fetch_page(url)
            filepath.write_text(html, encoding="utf-8")
            downloaded += 1
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append(item)

        time.sleep(REQUEST_DELAY)

    # Retry failed items
    if failed:
        print(f"\n--- Retry pass: {len(failed)} items (3s delay) ---\n")
        still_failed = []
        for i, item in enumerate(failed, 1):
            name = item["name"]
            url = item["url"]
            slug = slug_from_url(url)
            filepath = HTML_DIR / f"{slug}.html"
            print(f"[retry {i}/{len(failed)}] {name}...", end=" ", flush=True)
            try:
                html = fetch_page(url)
                filepath.write_text(html, encoding="utf-8")
                downloaded += 1
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
                still_failed.append(item)
            time.sleep(3.0)
        failed = still_failed

    print(f"\n=== Summary ===")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped (already cached): {skipped}")
    print(f"Failed: {len(failed)}")
    if failed:
        print("Still missing:")
        for item in failed:
            print(f"  - {item['name']}")

    # Now re-parse any locally saved pages that are missing from the DB
    print("\n=== Updating database from local files ===")
    import scraper
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")

    # Get items already in DB
    db_names = {r[0] for r in conn.execute("SELECT name FROM gear").fetchall()}

    updated = 0
    for item in items:
        slug = slug_from_url(item["url"])
        filepath = HTML_DIR / f"{slug}.html"

        if not filepath.exists():
            continue

        # Re-parse to update with fixed parser (for weapon detection, etc.)
        html = filepath.read_text(encoding="utf-8")
        gear_data = scraper.parse_gear_page(html, item["name"])
        scraper.insert_gear(conn, item, gear_data)
        updated += 1

    conn.close()
    print(f"Updated {updated} items in database from local cache.")

    # Final DB stats
    conn = sqlite3.connect(str(DB_PATH))
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
    conn.close()


if __name__ == "__main__":
    main()
