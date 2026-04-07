"""Stage 5: Parse cached gear HTML pages and insert into database."""

import json
import logging
import re
import sqlite3
from pathlib import Path

from utils import clean_html, parse_card_text, slug_from_url

log = logging.getLogger(__name__)


def parse_all_gear(items: list[dict], *, cache_dir: Path, db_path: Path):
    """Iterate all items, parse cached HTML, and insert into database.

    Commits every 50 items. Skips items whose cached HTML is missing.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    parsed = 0
    skipped = 0

    for i, item in enumerate(items, 1):
        slug = slug_from_url(item["url"])
        html_path = cache_dir / "gear" / f"{slug}.html"
        if not html_path.exists():
            log.debug("Cache miss for %s — skipping", item["name"])
            skipped += 1
            continue

        html = html_path.read_text(encoding="utf-8")
        gear_data = parse_gear_page(html, item["name"])
        _insert_gear(conn, item, gear_data)
        parsed += 1

        if parsed % 50 == 0:
            conn.commit()
            log.info("Parsed %d / %d items…", parsed, len(items))

    conn.commit()
    conn.close()
    log.info("Parsing complete: %d inserted, %d skipped (no cache)", parsed, skipped)


def parse_gear_page(html: str, name: str) -> dict:
    """Pure parser: extract gear fields from a wiki HTML page."""
    data = {"name": name}
    idx = html.find("mw-parser-output")
    if idx == -1:
        return data
    content = html[idx : idx + 60000]

    # Parse portable infobox
    infobox_match = re.search(
        r'<aside[^>]*class="portable-infobox[^"]*"[^>]*>(.*?)</aside>',
        content,
        re.DOTALL,
    )
    if infobox_match:
        infobox = infobox_match.group(1)

        # Weapon stats
        for stat in ("speed", "accuracy", "strength"):
            val_matches = re.findall(
                rf'<td[^>]*data-source="{stat}"[^>]*>(.*?)</td>',
                infobox,
                re.DOTALL,
            )
            if val_matches:
                data[stat] = clean_html(val_matches[-1]).strip()

        # hit_location
        hl_section = re.search(
            r'data-source="hit_location".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if hl_section:
            hl_html = hl_section.group(1)
            title_match = re.search(r'title="([^"]+)"', hl_html)
            if title_match:
                loc = title_match.group(1)
                if loc not in ("Hit Location", "Armor Points"):
                    data["hit_location"] = loc

        # armor_rating
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
            keywords = [
                k.strip() for k in raw_kw.replace("\n", ",").split(",") if k.strip()
            ]
            data["keywords"] = keywords

        # Special Rules
        sr_match = re.search(
            r'data-source="gear_special_rules".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if sr_match:
            raw_sr = clean_html(sr_match.group(1))
            special_rules = [
                r.strip() for r in raw_sr.replace("\n", ",").split(",") if r.strip()
            ]
            data["special_rules_names"] = special_rules

        # Gained by
        gb_match = re.search(
            r'data-source="gained_by".*?pi-data-value[^>]*>(.*?)</div>',
            infobox,
            re.DOTALL,
        )
        if gb_match:
            data["gained_by"] = clean_html(gb_match.group(1)).strip()

    # Card text
    card_text_match = re.search(
        r'id="Card_Text".*?</h\d>(.*?)'
        r"(?=<h\d|<!--\s*NewPP|<div\s+class=\"printfooter|<div\s+id=\"catlinks)",
        content,
        re.DOTALL,
    )
    if card_text_match:
        data["card_text"] = parse_card_text(card_text_match.group(1))

    # Crafting location
    craft_match = re.search(
        r"may be crafted once the\s*(.*?)\s*settlement location",
        content,
        re.DOTALL,
    )
    if craft_match:
        data["crafting_location"] = clean_html(craft_match.group(1)).strip()

    # Crafting cost
    cost_match = re.search(
        r'id="Cost".*?</h\d>(.*?)'
        r"(?=<h\d|<!--\s*NewPP|<div\s+class=\"printfooter|<div\s+id=\"catlinks)",
        content,
        re.DOTALL,
    )
    if cost_match:
        cost_text = clean_html(cost_match.group(1)).strip()
        cost_items = []
        for line in cost_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            qty_match = re.match(r"(\d+)x?\s+(.+)", line)
            if qty_match:
                cost_items.append(
                    {
                        "quantity": int(qty_match.group(1)),
                        "resource": qty_match.group(2).strip(),
                    }
                )
            elif line and not line.startswith("The "):
                cost_items.append({"quantity": 1, "resource": line})
        if cost_items:
            data["crafting_cost"] = cost_items

    # Determine type
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


def _insert_gear(conn, item_meta: dict, gear_data: dict):
    """Upsert a gear item using DELETE + INSERT (CASCADE cleans junction tables)."""
    merged = {**item_meta, **gear_data}
    name = merged["name"]
    version = merged.get("version", "1.5")
    special_rules_json = json.dumps(merged.get("special_rules_names", []))

    # Delete existing (CASCADE cleans junction tables)
    conn.execute("DELETE FROM gear WHERE name = ? AND version = ?", (name, version))

    cur = conn.execute(
        """INSERT INTO gear (name, version, type, expansion, category, url,
           speed, accuracy, strength, hit_location, armor_rating,
           affinity_top, affinity_bottom, affinity_left, affinity_right,
           gained_by, card_text, crafting_location, special_rules_names, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            version,
            merged.get("type"),
            merged.get("expansion"),
            merged.get("category"),
            merged.get("url"),
            merged.get("speed"),
            merged.get("accuracy"),
            merged.get("strength"),
            merged.get("hit_location"),
            merged.get("armor_rating"),
            merged.get("affinity_top"),
            merged.get("affinity_bottom"),
            merged.get("affinity_left"),
            merged.get("affinity_right"),
            merged.get("gained_by"),
            merged.get("card_text"),
            merged.get("crafting_location"),
            special_rules_json,
            json.dumps(merged, default=str),
        ),
    )
    gear_id = cur.lastrowid

    # Keywords (fix "weapon. melee" bug — split on ". ")
    for kw in merged.get("keywords", []):
        kw = kw.strip()
        if ". " in kw:
            for part in kw.split(". "):
                part = part.strip()
                if part:
                    conn.execute(
                        "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)",
                        (gear_id, part),
                    )
        elif kw:
            conn.execute(
                "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)",
                (gear_id, kw),
            )

    # Special rules
    for rule in merged.get("special_rules_names", []):
        rule = rule.strip()
        if rule:
            conn.execute(
                "INSERT INTO gear_special_rules (gear_id, rule) VALUES (?, ?)",
                (gear_id, rule),
            )

    # Crafting costs
    for cost in merged.get("crafting_cost", []):
        conn.execute(
            "INSERT INTO crafting_costs (gear_id, resource, quantity) VALUES (?, ?, ?)",
            (gear_id, cost["resource"], cost["quantity"]),
        )
