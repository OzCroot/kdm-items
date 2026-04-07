#!/usr/bin/env python3
"""KDM Gear Scraper Pipeline — run all stages end-to-end."""

import logging
import sqlite3
import time
from pathlib import Path

import config
import fetch_index
import fetch_pages
import parse_gear
import parse_definitions
import fetch_images

log = logging.getLogger("kdm-scraper")


def create_database(db_path: Path, schema_path: Path, fresh: bool = False):
    """Create DB from schema.sql. If fresh=True, delete existing DB first."""
    if fresh and db_path.exists():
        db_path.unlink()
        log.info("Deleted existing database.")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema_path.read_text())
    conn.close()


def print_summary(db_path: Path):
    """Print database statistics."""
    conn = sqlite3.connect(str(db_path))
    queries = [
        ("Total gear", "SELECT COUNT(*) FROM gear"),
        ("Weapons", "SELECT COUNT(*) FROM gear WHERE type='weapon'"),
        ("Armor", "SELECT COUNT(*) FROM gear WHERE type='armor'"),
        ("Items", "SELECT COUNT(*) FROM gear WHERE type='item'"),
        ("Other", "SELECT COUNT(*) FROM gear WHERE type='other'"),
        ("Unique keywords", "SELECT COUNT(DISTINCT keyword) FROM gear_keywords"),
        ("Special rules", "SELECT COUNT(DISTINCT rule) FROM gear_special_rules"),
        ("Crafting recipes", "SELECT COUNT(DISTINCT gear_id) FROM crafting_costs"),
        ("Keyword definitions", "SELECT COUNT(*) FROM keyword_definitions WHERE definition != ''"),
        ("Rule definitions", "SELECT COUNT(*) FROM special_rule_definitions WHERE definition != ''"),
        ("Location definitions", "SELECT COUNT(*) FROM settlement_locations WHERE definition != ''"),
        ("Card images", "SELECT COUNT(*) FROM gear WHERE image_path IS NOT NULL AND image_path != ''"),
    ]
    for label, query in queries:
        print(f"  {label}: {conn.execute(query).fetchone()[0]}")
    conn.close()


def main():
    args = config.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    start = time.monotonic()
    net_kwargs = {"delay": args.delay, "max_retries": args.max_retries}

    # Ensure cache directories exist
    for subdir in [
        "gear",
        "definitions/keywords",
        "definitions/special_rules",
        "definitions/settlement_locations",
    ]:
        (config.CACHE_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # Stage 1: Fetch gear index
    log.info("Stage 1: Fetching gear index...")
    items = fetch_index.fetch_gear_index(cache_dir=config.CACHE_DIR, **net_kwargs)
    log.info("Found %d gear items.", len(items))

    # Show expansion breakdown
    expansions: dict[str, int] = {}
    for item in items:
        expansions[item["expansion"]] = expansions.get(item["expansion"], 0) + 1
    for exp, count in expansions.items():
        log.info("  %s: %d items", exp, count)

    if not args.skip_download:
        # Stage 2: Download gear HTML pages
        log.info("Stage 2: Downloading gear pages...")
        result = fetch_pages.download_gear_pages(
            items, cache_dir=config.CACHE_DIR, **net_kwargs,
        )
        log.info(
            "Downloaded %d, skipped %d, failed %d.",
            result.downloaded, result.skipped, len(result.failed),
        )

        # Stage 3: Download definition HTML pages
        log.info("Stage 3: Downloading definition pages...")
        for cat_slug, cat_url in [
            ("keywords", f"{config.BASE_URL}/wiki/Category:Keywords"),
            ("special_rules", f"{config.BASE_URL}/wiki/Category:Gear_Special_Rules"),
            ("settlement_locations", f"{config.BASE_URL}/wiki/Category:Settlement_Locations"),
        ]:
            pages = fetch_pages.download_definition_pages(
                cat_url, cat_slug, cache_dir=config.CACHE_DIR, **net_kwargs,
            )
            log.info("  %s: cached %d pages", cat_slug, len(pages))

    # Stage 4: Create database
    log.info("Stage 4: Creating database at %s...", config.DB_PATH)
    create_database(config.DB_PATH, config.SCHEMA_PATH, fresh=args.fresh_db)

    # Stage 5: Parse gear pages
    log.info("Stage 5: Parsing gear pages...")
    parse_gear.parse_all_gear(items, cache_dir=config.CACHE_DIR, db_path=config.DB_PATH)

    # Stage 6: Parse definition pages
    log.info("Stage 6: Parsing definition pages...")
    parse_definitions.parse_all_definitions(
        cache_dir=config.CACHE_DIR, db_path=config.DB_PATH,
    )

    if not args.skip_images:
        # Stage 7: Download card images
        log.info("Stage 7: Downloading card images...")
        fetch_images.download_card_images(
            cache_dir=config.CACHE_DIR, db_path=config.DB_PATH,
            images_dir=config.IMAGES_DIR, **net_kwargs,
        )

        # Stage 8: Download icon images
        log.info("Stage 8: Downloading icon images...")
        fetch_images.download_icon_images(
            cache_dir=config.CACHE_DIR, db_path=config.DB_PATH,
            images_dir=config.IMAGES_DIR, **net_kwargs,
        )

    elapsed = time.monotonic() - start
    log.info("Done in %.1fs.", elapsed)
    print("\n=== Summary ===")
    print_summary(config.DB_PATH)


if __name__ == "__main__":
    main()
