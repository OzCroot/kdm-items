"""Stages 7-8: Download card images and icon images."""

import logging
import re
import sqlite3
from pathlib import Path

import net
from utils import extract_icon_urls, slug_from_url

log = logging.getLogger(__name__)

ICON_PATTERNS = ["Icon.png", "icon.png", "Aff.png", "aff.png", "_aff."]


def download_card_images(
    *,
    cache_dir: Path,
    db_path: Path,
    images_dir: Path,
    delay: float = 1.0,
    max_retries: int = 3,
):
    """Download card images for all gear items in the database.

    Reads cached HTML to extract the card image URL from the infobox,
    downloads to images_dir/cards/{slug}.{ext}, and updates DB fields
    gear.image_url and gear.image_path.
    """
    cards_dir = images_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, name, url FROM gear").fetchall()
    downloaded = 0
    skipped = 0
    failed = 0

    for gear_id, name, url in rows:
        slug = slug_from_url(url).lower()

        # Check if image already exists
        existing = list(cards_dir.glob(f"{slug}.*"))
        if existing:
            skipped += 1
            continue

        # Read cached HTML
        cache_slug = slug_from_url(url)
        html_path = cache_dir / "gear" / f"{cache_slug}.html"
        if not html_path.exists():
            log.debug("No cached HTML for %s — skipping image", name)
            skipped += 1
            continue

        html = html_path.read_text(encoding="utf-8")
        image_url = _extract_image_url(html)
        if not image_url:
            log.debug("No card image found for %s", name)
            skipped += 1
            continue

        ext = _get_extension(image_url)
        dest = cards_dir / f"{slug}{ext}"

        if net.download_binary(image_url, dest, delay=delay, max_retries=max_retries):
            conn.execute(
                "UPDATE gear SET image_url = ?, image_path = ? WHERE id = ?",
                (image_url, str(dest), gear_id),
            )
            conn.commit()
            downloaded += 1
            if downloaded % 20 == 0:
                log.info("Downloaded %d card images…", downloaded)
        else:
            failed += 1

    conn.close()
    log.info(
        "Card images complete: %d downloaded, %d skipped, %d failed",
        downloaded,
        skipped,
        failed,
    )


def download_icon_images(
    *,
    cache_dir: Path,
    db_path: Path,
    images_dir: Path,
    delay: float = 1.0,
    max_retries: int = 3,
):
    """Download unique icon images found in card text sections.

    Scans all cached gear HTML for icon images, collects unique icon URLs,
    downloads to images_dir/icons/{tag}.{ext}, and updates the
    card_text_icons table with icon_url and icon_path.
    """
    icons_dir = images_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Scan all cached gear HTML for icon URLs
    gear_dir = cache_dir / "gear"
    all_icons: dict[str, str] = {}  # tag -> url

    if gear_dir.is_dir():
        for html_path in sorted(gear_dir.glob("*.html")):
            html = html_path.read_text(encoding="utf-8")
            icons = extract_icon_urls(html)
            for tag, url in icons.items():
                if tag not in all_icons:
                    all_icons[tag] = url

    log.info("Found %d unique icon tags across all gear pages", len(all_icons))

    conn = sqlite3.connect(db_path)
    downloaded = 0
    skipped = 0
    failed = 0

    for tag, url in all_icons.items():
        # Update icon_url in DB
        conn.execute(
            "UPDATE card_text_icons SET icon_url = ? WHERE tag = ?", (url, tag)
        )

        ext = _get_extension(url)
        dest = icons_dir / f"{tag}{ext}"

        # Skip if already downloaded
        if dest.exists():
            conn.execute(
                "UPDATE card_text_icons SET icon_path = ? WHERE tag = ?",
                (str(dest), tag),
            )
            skipped += 1
            continue

        if net.download_binary(url, dest, delay=delay, max_retries=max_retries):
            conn.execute(
                "UPDATE card_text_icons SET icon_path = ? WHERE tag = ?",
                (str(dest), tag),
            )
            downloaded += 1
        else:
            failed += 1

    conn.commit()
    conn.close()
    log.info(
        "Icon images complete: %d downloaded, %d skipped, %d failed",
        downloaded,
        skipped,
        failed,
    )


def _extract_image_url(html: str) -> str | None:
    """Extract the card image URL from the portable infobox."""
    infobox = re.search(
        r'<aside[^>]*class="portable-infobox[^"]*"[^>]*>(.*?)</aside>',
        html,
        re.DOTALL,
    )
    if not infobox:
        return None
    imgs = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', infobox.group(1))
    card_imgs = [i for i in imgs if not any(p in i for p in ICON_PATTERNS)]
    if not card_imgs:
        return None
    scaled = [i for i in card_imgs if "scale-to-width" in i]
    url = scaled[0] if scaled else card_imgs[0]
    url = re.sub(r"/scale-to-width-down/\d+", "", url)
    return url


def _get_extension(url: str) -> str:
    """Extract the file extension from a wiki image URL."""
    match = re.search(r"\.(\w{3,4})/revision", url)
    if match:
        return f".{match.group(1).lower()}"
    return ".png"
