"""Central configuration for the KDM gear scraper."""

import argparse
import os
from pathlib import Path

BASE_URL = "https://kingdomdeath.fandom.com"
GEAR_INDEX_URL = f"{BASE_URL}/wiki/Gear"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = Path(os.environ.get("DB_PATH", PROJECT_ROOT / "data" / "kdm_gear.db"))
CACHE_DIR = Path(os.environ.get("CACHE_DIR", Path(__file__).parent / "cache"))
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the scraper."""
    parser = argparse.ArgumentParser(description="KDM gear scraper")
    parser.add_argument(
        "--delay",
        type=float,
        default=float(os.environ.get("SCRAPER_DELAY", "1.0")),
        help="delay between requests in seconds (default: 1.0, env: SCRAPER_DELAY)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="maximum number of retries per request (default: 3)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="skip network fetches, parse from existing cache",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="skip image download stages",
    )
    parser.add_argument(
        "--fresh-db",
        action="store_true",
        help="delete and recreate database",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="enable debug logging",
    )
    return parser.parse_args()
