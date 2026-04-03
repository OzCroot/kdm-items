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
