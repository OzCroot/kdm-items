"""Stage 6: Parse cached definition HTML pages and populate definition tables."""

import logging
import re
import sqlite3
from pathlib import Path

from utils import clean_html

log = logging.getLogger(__name__)

# Each category: (cache subdir, DB table, key column, SQL to get known names)
_CATEGORIES = [
    (
        "keywords",
        "keyword_definitions",
        "keyword",
        "SELECT DISTINCT keyword FROM gear_keywords",
    ),
    (
        "special_rules",
        "special_rule_definitions",
        "rule",
        "SELECT DISTINCT rule FROM gear_special_rules",
    ),
    (
        "settlement_locations",
        "settlement_locations",
        "name",
        "SELECT DISTINCT crafting_location FROM gear "
        "WHERE crafting_location IS NOT NULL AND crafting_location != ''",
    ),
]


def parse_all_definitions(*, cache_dir: Path, db_path: Path):
    """Parse all three definition categories from cached HTML into the database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    for subdir, table, key_col, source_query in _CATEGORIES:
        log.info("Processing definitions: %s", subdir)

        # 1. Get known names from gear data
        db_names = {row[0] for row in conn.execute(source_query).fetchall()}
        log.info("  %d known %s names from gear data", len(db_names), subdir)

        # 2. Seed the definition table with known names
        for name in db_names:
            conn.execute(
                f"INSERT OR IGNORE INTO {table} ({key_col}) VALUES (?)", (name,)
            )
        conn.commit()

        # 3. Read cached HTML files
        html_dir = cache_dir / "definitions" / subdir
        if not html_dir.is_dir():
            log.warning("  Cache directory missing: %s", html_dir)
            continue

        html_files = sorted(html_dir.glob("*.html"))
        matched = 0
        unmatched = 0

        for html_path in html_files:
            if html_path.name == "_category.html":
                continue

            # Derive wiki title from filename (reverse slug)
            wiki_title = html_path.stem.replace("_", " ")
            html = html_path.read_text(encoding="utf-8")
            definition = extract_definition(html)

            if not definition:
                continue

            # 4. Match wiki title to a DB name and update
            db_name = _match_db_name(wiki_title, db_names)
            if db_name:
                conn.execute(
                    f"UPDATE {table} SET definition = ? WHERE {key_col} = ?",
                    (definition, db_name),
                )
                matched += 1
            else:
                unmatched += 1

        conn.commit()
        log.info(
            "  %s: %d matched, %d unmatched out of %d files",
            subdir,
            matched,
            unmatched,
            len(html_files),
        )

    conn.close()
    log.info("Definition parsing complete")


def extract_definition(html: str) -> str:
    """Pure parser: extract intro text before the first h2 heading."""
    idx = html.find("mw-parser-output")
    if idx == -1:
        return ""
    content = html[idx : idx + 10000]
    first_h2 = content.find("<h2")
    if first_h2 > 0:
        content = content[:first_h2]
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)
    text = "\n".join(clean_html(p) for p in paragraphs)
    text = text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def _match_db_name(wiki_title: str, db_names: set[str]) -> str | None:
    """Fuzzy-match a wiki page title to a known DB name."""
    # Exact match
    if wiki_title in db_names:
        return wiki_title

    # Strip parenthetical suffix
    base = re.sub(r"\s*\([^)]+\)\s*$", "", wiki_title).strip()
    if base in db_names:
        return base

    # Handle "X" placeholder (e.g. "Sharp X" -> "Sharp 1")
    if " X" in wiki_title or wiki_title.endswith(" X"):
        pattern = wiki_title.replace(" X", "")
        matches = [n for n in db_names if n.startswith(pattern)]
        if matches:
            return matches[0]

    # Case-insensitive fallback
    lower_map = {n.lower(): n for n in db_names}
    if wiki_title.lower() in lower_map:
        return lower_map[wiki_title.lower()]
    if base.lower() in lower_map:
        return lower_map[base.lower()]

    return None
