"""
Schema migration: adds version, image, and affinity columns to the gear table.
Also fixes the 'weapon. melee' keyword bug.
Safe to run multiple times — checks for existing columns before altering.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))


def get_existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def migrate(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")

    existing = get_existing_columns(conn, "gear")

    # --- Add new columns ---
    new_columns = [
        ("version", "TEXT DEFAULT '1.5'"),
        ("image_url", "TEXT"),
        ("image_path", "TEXT"),
        ("affinity_top", "TEXT"),
        ("affinity_bottom", "TEXT"),
        ("affinity_left", "TEXT"),
        ("affinity_right", "TEXT"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing:
            print(f"  Adding column: gear.{col_name}")
            conn.execute(f"ALTER TABLE gear ADD COLUMN {col_name} {col_def}")
        else:
            print(f"  Column already exists: gear.{col_name}")

    # --- Update unique constraint ---
    # SQLite doesn't support ALTER TABLE to change constraints, so we create
    # a unique index instead. Drop the old one if it exists.
    conn.execute("DROP INDEX IF EXISTS idx_gear_name_version")
    conn.execute("CREATE UNIQUE INDEX idx_gear_name_version ON gear(name, version)")
    print("  Created unique index: (name, version)")

    # --- Create gear_special_rules table ---
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "gear_special_rules" not in tables:
        print("  Creating table: gear_special_rules")
        conn.execute("""
            CREATE TABLE gear_special_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gear_id INTEGER NOT NULL REFERENCES gear(id),
                rule TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_gear_special_rules_gear_id ON gear_special_rules(gear_id)")
        conn.execute("CREATE INDEX idx_gear_special_rules_rule ON gear_special_rules(rule)")

        # Populate from existing special_rules_names JSON column
        import json
        rows = conn.execute(
            "SELECT id, special_rules_names FROM gear WHERE special_rules_names IS NOT NULL AND special_rules_names != '[]'"
        ).fetchall()
        insert = conn.prepare("INSERT INTO gear_special_rules (gear_id, rule) VALUES (?, ?)") if False else None
        count = 0
        for gear_id, sr_json in rows:
            for rule in json.loads(sr_json):
                rule = rule.strip()
                if rule:
                    conn.execute("INSERT INTO gear_special_rules (gear_id, rule) VALUES (?, ?)", (gear_id, rule))
                    count += 1
        print(f"  Populated {count} special rules from {len(rows)} items")
    else:
        print("  Table already exists: gear_special_rules")

    # --- Create keyword_definitions table ---
    if "keyword_definitions" not in tables:
        print("  Creating table: keyword_definitions")
        conn.execute("""
            CREATE TABLE keyword_definitions (
                keyword TEXT PRIMARY KEY,
                definition TEXT NOT NULL DEFAULT ''
            )
        """)
        # Seed with all existing keywords
        keywords = conn.execute("SELECT DISTINCT keyword FROM gear_keywords").fetchall()
        for (kw,) in keywords:
            conn.execute("INSERT OR IGNORE INTO keyword_definitions (keyword) VALUES (?)", (kw,))
        print(f"  Seeded {len(keywords)} keyword definitions")
    else:
        print("  Table already exists: keyword_definitions")

    # --- Create special_rule_definitions table ---
    if "special_rule_definitions" not in tables:
        print("  Creating table: special_rule_definitions")
        conn.execute("""
            CREATE TABLE special_rule_definitions (
                rule TEXT PRIMARY KEY,
                definition TEXT NOT NULL DEFAULT ''
            )
        """)
        # Seed with all existing rules
        rules = conn.execute("SELECT DISTINCT rule FROM gear_special_rules").fetchall()
        for (rule,) in rules:
            conn.execute("INSERT OR IGNORE INTO special_rule_definitions (rule) VALUES (?)", (rule,))
        print(f"  Seeded {len(rules)} special rule definitions")
    else:
        print("  Table already exists: special_rule_definitions")

    # --- Create settlement_locations table ---
    if "settlement_locations" not in tables:
        print("  Creating table: settlement_locations")
        conn.execute("""
            CREATE TABLE settlement_locations (
                name TEXT PRIMARY KEY,
                definition TEXT NOT NULL DEFAULT ''
            )
        """)
        # Seed from existing crafting_location values on gear
        locations = conn.execute(
            "SELECT DISTINCT crafting_location FROM gear WHERE crafting_location IS NOT NULL AND crafting_location != ''"
        ).fetchall()
        for (loc,) in locations:
            conn.execute("INSERT OR IGNORE INTO settlement_locations (name) VALUES (?)", (loc.strip(),))
        print(f"  Seeded {len(locations)} settlement locations")
    else:
        print("  Table already exists: settlement_locations")

    # --- Create card_text_icons table ---
    if "card_text_icons" not in tables:
        print("  Creating table: card_text_icons")
        conn.execute("""
            CREATE TABLE card_text_icons (
                tag TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                icon_url TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT ''
            )
        """)
        icons = [
            ("activation", "Activation"),
            ("movement", "Movement"),
            ("reaction", "Reaction"),
            ("blue_affinity", "Blue Affinity"),
            ("red_affinity", "Red Affinity"),
            ("green_affinity", "Green Affinity"),
            ("blue_puzzle", "Blue Puzzle Affinity"),
            ("red_puzzle", "Red Puzzle Affinity"),
            ("green_puzzle", "Green Puzzle Affinity"),
            ("ai_card", "AI Card"),
            ("monster_level", "Monster Level"),
            ("pumpkin", "Pumpkin"),
        ]
        for tag, display_name in icons:
            conn.execute("INSERT INTO card_text_icons (tag, display_name) VALUES (?, ?)", (tag, display_name))
        print(f"  Seeded {len(icons)} card text icons")
    else:
        print("  Table already exists: card_text_icons")

    # --- Create expansions table ---
    if "expansions" not in tables:
        print("  Creating table: expansions")
        conn.execute("""
            CREATE TABLE expansions (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT ''
            )
        """)
        existing = conn.execute("SELECT DISTINCT expansion FROM gear WHERE expansion IS NOT NULL AND expansion != ''").fetchall()
        for (exp,) in existing:
            conn.execute("INSERT OR IGNORE INTO expansions (name) VALUES (?)", (exp.strip(),))
        print(f"  Seeded {len(existing)} expansions")
    else:
        print("  Table already exists: expansions")

    # --- Create versions table ---
    if "versions" not in tables:
        print("  Creating table: versions")
        conn.execute("""
            CREATE TABLE versions (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL DEFAULT ''
            )
        """)
        # Seed with known KDM editions
        known_versions = [
            ("1.0", "Original 2015 Kickstarter release"),
            ("1.3", "First major reprint / update"),
            ("1.5", "2017 revised edition"),
            ("1.6", "Gamblers Chest era update"),
        ]
        for name, desc in known_versions:
            conn.execute("INSERT OR IGNORE INTO versions (name, description) VALUES (?, ?)", (name, desc))
        # Also seed any versions found in gear data
        existing = conn.execute("SELECT DISTINCT version FROM gear WHERE version IS NOT NULL AND version != ''").fetchall()
        for (v,) in existing:
            conn.execute("INSERT OR IGNORE INTO versions (name) VALUES (?)", (v,))
        print(f"  Seeded {len(known_versions)} versions")
    else:
        print("  Table already exists: versions")

    # --- Fix 'weapon. melee' keyword bug ---
    rows = conn.execute(
        "SELECT id, gear_id FROM gear_keywords WHERE keyword = 'weapon. melee'"
    ).fetchall()
    if rows:
        for row_id, gear_id in rows:
            conn.execute("DELETE FROM gear_keywords WHERE id = ?", (row_id,))
            # Add the two correct keywords if they don't already exist
            for kw in ("weapon", "melee"):
                exists = conn.execute(
                    "SELECT 1 FROM gear_keywords WHERE gear_id = ? AND keyword = ?",
                    (gear_id, kw),
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)",
                        (gear_id, kw),
                    )
            print(f"  Fixed 'weapon. melee' keyword for gear_id={gear_id}")
    else:
        print("  No 'weapon. melee' keyword bug found")

    conn.commit()
    conn.close()


def main():
    print(f"Migrating: {DB_PATH}")
    if not DB_PATH.exists():
        print("ERROR: Database not found")
        return
    migrate(DB_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
