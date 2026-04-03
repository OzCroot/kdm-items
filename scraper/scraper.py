"""
Kingdom Death Monster - Gear Scraper
Scrapes all gear items from the KDM Fandom wiki and stores them in a SQLite database.
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
REQUEST_DELAY = 0.5  # seconds between requests to be polite


def fetch_page(url: str) -> str:
    """Fetch a wiki page and return its HTML content."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def clean_html(text: str) -> str:
    """Strip HTML tags and clean whitespace."""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n ", "\n", text)
    text = text.strip()
    return text


# ---------------------------------------------------------------------------
# Step 1: Parse the gear index page to get all item URLs by category
# ---------------------------------------------------------------------------

def parse_gear_index(html: str) -> list[dict]:
    """Parse the Gear index page and extract all gear items with their categories."""
    idx = html.find("mw-parser-output")
    if idx == -1:
        raise ValueError("Could not find content area in gear index page")

    content = html[idx:]

    # Find the "List of Gear" section - everything after it contains the item lists
    list_idx = content.find('id="List_of_Gear"')
    if list_idx == -1:
        raise ValueError("Could not find 'List of Gear' section")

    content = content[list_idx:]

    # Parse sections: h3 = expansion, h4 = crafting location / sub-category
    # Each section contains links to gear items
    items = []
    current_expansion = "Core Game"
    current_category = ""

    # Split by headings
    parts = re.split(r"(<h[234][^>]*>.*?</h[234]>)", content, flags=re.DOTALL)

    for i, part in enumerate(parts):
        # Check if this is a heading
        h_match = re.match(r"<(h[234])[^>]*>(.*?)</\1>", part, re.DOTALL)
        if h_match:
            level = h_match.group(1)
            heading_text = clean_html(h_match.group(2)).replace("[]", "").strip()

            if level == "h2":
                # Top-level: expansion name
                current_expansion = heading_text
                current_category = ""
            elif level == "h3":
                # Could be expansion or category depending on context
                # If it contains "Expansion" it's an expansion
                if "Expansion" in heading_text or heading_text in ("Core Game",):
                    current_expansion = heading_text
                    current_category = ""
                else:
                    current_category = heading_text
            elif level == "h4":
                current_category = heading_text
            continue

        # Extract gear links from this section
        links = re.findall(
            r'href="(/wiki/[^"#]+)"[^>]*title="([^"]+)"',
            part,
        )
        for href, title in links:
            # Filter out non-gear pages (categories, concepts, etc.)
            slug = href.split("/wiki/")[1] if "/wiki/" in href else ""
            if ":" in slug:
                continue
            # Skip known concept/mechanic pages
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
            if slug in skip_pages:
                continue

            # Also skip if title matches known concept names
            if title in ("Bone", "Savage", "Frail"):
                continue

            items.append({
                "name": unescape(title),
                "url": f"{BASE_URL}{href}",
                "expansion": current_expansion,
                "category": current_category,
            })

    # Deduplicate by URL
    seen = set()
    unique = []
    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique


# ---------------------------------------------------------------------------
# Step 2: Parse individual gear pages
# ---------------------------------------------------------------------------

def parse_gear_page(html: str, name: str) -> dict:
    """Parse a single gear page and extract all data from the infobox and body."""
    data = {"name": name}

    idx = html.find("mw-parser-output")
    if idx == -1:
        return data

    content = html[idx: idx + 60000]

    # --- Parse the portable infobox ---
    infobox_match = re.search(
        r'<aside[^>]*class="portable-infobox[^"]*"[^>]*>(.*?)</aside>',
        content,
        re.DOTALL,
    )
    if infobox_match:
        infobox = infobox_match.group(1)

        # Weapon stats: speed, accuracy, strength
        # These appear in <td> tags with data-source="X" in the value row
        for stat in ("speed", "accuracy", "strength"):
            val_matches = re.findall(
                rf'<td[^>]*data-source="{stat}"[^>]*>(.*?)</td>',
                infobox,
                re.DOTALL,
            )
            if val_matches:
                data[stat] = clean_html(val_matches[-1]).strip()

        # Armor stats: hit_location, armor_rating
        # These use nested divs: outer <div data-source="X"> contains inner <div class="pi-data-value">
        # hit_location: The location name is in a link title attribute (uses icon font)
        hl_section = re.search(
            r'data-source="hit_location".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if hl_section:
            hl_html = hl_section.group(1)
            # Extract from link title (e.g., title="Legs")
            title_match = re.search(r'title="([^"]+)"', hl_html)
            if title_match:
                loc = title_match.group(1)
                # Filter out generic titles
                if loc not in ("Hit Location", "Armor Points"):
                    data["hit_location"] = loc

        # armor_rating: number is in the text, often styled with custom font
        ar_section = re.search(
            r'data-source="armor_rating".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if ar_section:
            ar_text = clean_html(ar_section.group(1))
            nums = re.findall(r"(\d+)", ar_text)
            if nums:
                data["armor_rating"] = nums[0]

        # Keywords
        kw_match = re.search(
            r'data-source="gear_keywords".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if kw_match:
            raw_kw = clean_html(kw_match.group(1))
            keywords = [k.strip() for k in raw_kw.replace("\n", ",").split(",") if k.strip()]
            data["keywords"] = keywords

        # Special Rules (names only from infobox)
        sr_match = re.search(
            r'data-source="gear_special_rules".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if sr_match:
            raw_sr = clean_html(sr_match.group(1))
            special_rules = [r.strip() for r in raw_sr.replace("\n", ",").split(",") if r.strip()]
            data["special_rules_names"] = special_rules

        # Gained by
        gb_match = re.search(
            r'data-source="gained_by".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if gb_match:
            data["gained_by"] = clean_html(gb_match.group(1)).strip()

        # Affinity info - look for colored affinity squares
        # Check for affinity data in the infobox
        aff_section = re.search(
            r'data-source="affinity_(?:right|left|top|bottom)"(.*?)(?=data-source="|$)',
            infobox,
            re.DOTALL,
        )

    # --- Parse card text from the body ---
    card_text_match = re.search(
        r'id="Card_Text".*?</h\d>(.*?)(?=<h\d|<div\s+class="printfooter)',
        content,
        re.DOTALL,
    )
    if card_text_match:
        data["card_text"] = clean_html(card_text_match.group(1)).strip()

    # --- Parse crafting location ---
    craft_match = re.search(
        r"may be crafted once the\s*(.*?)\s*settlement location",
        content,
        re.DOTALL,
    )
    if craft_match:
        data["crafting_location"] = clean_html(craft_match.group(1)).strip()

    # --- Parse crafting cost ---
    cost_match = re.search(
        r'id="Cost".*?</h\d>(.*?)(?=<h\d|<div\s+class="printfooter)',
        content,
        re.DOTALL,
    )
    if cost_match:
        cost_text = clean_html(cost_match.group(1)).strip()
        # Parse individual cost items like "1x Bone\n1x Hide"
        cost_items = []
        for line in cost_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            qty_match = re.match(r"(\d+)x?\s+(.+)", line)
            if qty_match:
                cost_items.append({
                    "quantity": int(qty_match.group(1)),
                    "resource": qty_match.group(2).strip(),
                })
            elif line and not line.startswith("The "):
                cost_items.append({"quantity": 1, "resource": line})
        if cost_items:
            data["crafting_cost"] = cost_items

    # --- Determine gear type ---
    keywords = data.get("keywords", [])
    kw_lower = [k.lower() for k in keywords]
    if "speed" in data:
        data["type"] = "weapon"
    elif "armor_rating" in data or "armor" in kw_lower:
        data["type"] = "armor"
    elif "item" in kw_lower or "consumable" in kw_lower:
        data["type"] = "item"
    else:
        data["type"] = "other"

    return data


# ---------------------------------------------------------------------------
# Step 3: Database
# ---------------------------------------------------------------------------

def create_database(db_path: Path) -> sqlite3.Connection:
    """Create the SQLite database with the gear schema."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS gear (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT,              -- weapon, armor, item, other
            expansion TEXT,
            category TEXT,          -- crafting location or sub-category
            url TEXT,

            -- Weapon stats
            speed TEXT,
            accuracy TEXT,
            strength TEXT,

            -- Armor stats
            hit_location TEXT,
            armor_rating TEXT,

            -- Other
            gained_by TEXT,
            card_text TEXT,
            crafting_location TEXT,
            special_rules_names TEXT,  -- JSON array of rule names

            raw_json TEXT           -- full scraped data as JSON backup
        );

        CREATE TABLE IF NOT EXISTS gear_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gear_id INTEGER NOT NULL REFERENCES gear(id),
            keyword TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS crafting_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gear_id INTEGER NOT NULL REFERENCES gear(id),
            resource TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_gear_name ON gear(name);
        CREATE INDEX IF NOT EXISTS idx_gear_type ON gear(type);
        CREATE INDEX IF NOT EXISTS idx_gear_expansion ON gear(expansion);
        CREATE INDEX IF NOT EXISTS idx_gear_keywords_keyword ON gear_keywords(keyword);
        CREATE INDEX IF NOT EXISTS idx_gear_keywords_gear_id ON gear_keywords(gear_id);
        CREATE INDEX IF NOT EXISTS idx_crafting_costs_gear_id ON crafting_costs(gear_id);
    """)

    conn.commit()
    return conn


def insert_gear(conn: sqlite3.Connection, item_meta: dict, gear_data: dict):
    """Insert a gear item and its related data into the database."""
    cur = conn.cursor()

    # Merge meta (from index) with scraped data
    merged = {**item_meta, **gear_data}

    special_rules_json = json.dumps(merged.get("special_rules_names", []))
    name = merged.get("name")

    # Check if gear already exists
    existing = cur.execute("SELECT id FROM gear WHERE name = ?", (name,)).fetchone()
    if existing:
        gear_id = existing[0]
        cur.execute(
            """UPDATE gear SET type=?, expansion=?, category=?, url=?,
               speed=?, accuracy=?, strength=?,
               hit_location=?, armor_rating=?,
               gained_by=?, card_text=?, crafting_location=?,
               special_rules_names=?, raw_json=?
               WHERE id=?""",
            (
                merged.get("type"), merged.get("expansion"), merged.get("category"),
                merged.get("url"), merged.get("speed"), merged.get("accuracy"),
                merged.get("strength"), merged.get("hit_location"),
                merged.get("armor_rating"), merged.get("gained_by"),
                merged.get("card_text"), merged.get("crafting_location"),
                special_rules_json, json.dumps(merged, default=str),
                gear_id,
            ),
        )
        # Clear old related data
        cur.execute("DELETE FROM gear_keywords WHERE gear_id = ?", (gear_id,))
        cur.execute("DELETE FROM crafting_costs WHERE gear_id = ?", (gear_id,))
    else:
        cur.execute(
            """INSERT INTO gear
               (name, type, expansion, category, url,
                speed, accuracy, strength,
                hit_location, armor_rating,
                gained_by, card_text, crafting_location,
                special_rules_names, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, merged.get("type"), merged.get("expansion"),
                merged.get("category"), merged.get("url"),
                merged.get("speed"), merged.get("accuracy"),
                merged.get("strength"), merged.get("hit_location"),
                merged.get("armor_rating"), merged.get("gained_by"),
                merged.get("card_text"), merged.get("crafting_location"),
                special_rules_json, json.dumps(merged, default=str),
            ),
        )
        gear_id = cur.lastrowid

    # Insert keywords
    for kw in merged.get("keywords", []):
        cur.execute(
            "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)",
            (gear_id, kw.strip()),
        )

    # Insert crafting costs
    for cost in merged.get("crafting_cost", []):
        cur.execute(
            "INSERT INTO crafting_costs (gear_id, resource, quantity) VALUES (?, ?, ?)",
            (gear_id, cost["resource"], cost["quantity"]),
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Kingdom Death Monster Gear Scraper ===\n")

    # Step 1: Fetch and parse the gear index
    print("Fetching gear index page...")
    index_html = fetch_page(GEAR_INDEX_URL)
    items = parse_gear_index(index_html)
    print(f"Found {len(items)} gear items across all expansions.\n")

    # Show category breakdown
    expansions = {}
    for item in items:
        exp = item["expansion"]
        expansions[exp] = expansions.get(exp, 0) + 1
    for exp, count in expansions.items():
        print(f"  {exp}: {count} items")
    print()

    # Step 2: Create database
    print(f"Creating database at {DB_PATH}...")
    conn = create_database(DB_PATH)
    print("Database ready.\n")

    # Step 3: Scrape each gear page with retry logic
    total = len(items)
    failed = []

    def scrape_item(item, conn, attempt_label=""):
        name = item["name"]
        url = item["url"]
        html = fetch_page(url)
        gear_data = parse_gear_page(html, name)
        insert_gear(conn, item, gear_data)
        return gear_data

    for i, item in enumerate(items, 1):
        pct = i * 100 // total
        print(f"[{i}/{total}] ({pct}%) Scraping: {item['name']}...", end=" ", flush=True)

        try:
            gear_data = scrape_item(item, conn)
            print(f"OK ({gear_data.get('type', '?')})")
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append(item)

        time.sleep(REQUEST_DELAY)

    # Retry pass for failed items with longer delays
    if failed:
        print(f"\n--- Retry pass: {len(failed)} failed items (2s delay) ---\n")
        still_failed = []
        for i, item in enumerate(failed, 1):
            print(f"[retry {i}/{len(failed)}] {item['name']}...", end=" ", flush=True)
            try:
                gear_data = scrape_item(item, conn)
                print(f"OK ({gear_data.get('type', '?')})")
            except Exception as e:
                print(f"FAILED: {e}")
                still_failed.append({"name": item["name"], "url": item["url"], "error": str(e)})
            time.sleep(2.0)
        failed_items = still_failed
    else:
        failed_items = []

    conn.close()

    # Summary
    success_count = total - len(failed_items)
    print(f"\n=== Done ===")
    print(f"Successfully scraped: {success_count}/{total}")
    if failed_items:
        print(f"Permanently failed ({len(failed_items)}):")
        for err in failed_items:
            print(f"  - {err['name']}: {err['error']}")

    # Quick DB stats
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
