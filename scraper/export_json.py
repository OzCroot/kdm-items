"""
Export all gear data to a static JSON file for the gear grid app.
"""

import os
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
OUTPUT_PATH = Path(__file__).parent.parent / "grid" / "public" / "gear-data.json"


def export():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    items = []
    for row in conn.execute("SELECT * FROM gear ORDER BY name").fetchall():
        gear = dict(row)
        gear_id = gear["id"]

        # Keywords
        keywords = [r["keyword"] for r in conn.execute(
            "SELECT keyword FROM gear_keywords WHERE gear_id = ?", (gear_id,)
        ).fetchall()]

        # Special rules
        rules = [r["rule"] for r in conn.execute(
            "SELECT rule FROM gear_special_rules WHERE gear_id = ?", (gear_id,)
        ).fetchall()]

        # Crafting costs
        costs = [{"resource": r["resource"], "quantity": r["quantity"]} for r in conn.execute(
            "SELECT resource, quantity FROM crafting_costs WHERE gear_id = ?", (gear_id,)
        ).fetchall()]

        # Remove raw_json and special_rules_names (redundant)
        del gear["raw_json"]
        del gear["special_rules_names"]

        gear["keywords"] = keywords
        gear["special_rules"] = rules
        gear["crafting_costs"] = costs

        items.append(gear)

    conn.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Exported {len(items)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    export()
