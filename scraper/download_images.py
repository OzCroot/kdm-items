"""
Extract card image URLs from cached HTML pages and download them locally.
Stores image_url and image_path in the database.
"""

import os
import re
import time
import sqlite3
import urllib.request
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
HTML_DIR = Path(os.environ.get("HTML_DIR", Path(__file__).parent / "html_pages"))
IMAGES_DIR = Path(os.environ.get("IMAGES_DIR", Path(__file__).parent.parent / "data" / "images"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_DELAY = 1.0

# Small icons and affinity images to filter out
ICON_PATTERNS = ["Icon.png", "icon.png", "Aff.png", "aff.png", "_aff."]


def slug_from_url(url: str) -> str:
    """Convert wiki URL to lowercase slug for filenames."""
    slug = url.split("/wiki/")[-1] if "/wiki/" in url else url
    slug = slug.replace("%27", "'").replace("%26", "&").replace("%28", "(").replace("%29", ")")
    slug = re.sub(r'[<>:"/\\|?*]', '_', slug)
    return slug.lower()


def extract_image_url(html: str) -> str | None:
    """Extract the card image URL from an HTML page's infobox."""
    infobox = re.search(
        r'<aside[^>]*class="portable-infobox[^"]*"[^>]*>(.*?)</aside>',
        html,
        re.DOTALL,
    )
    if not infobox:
        return None

    imgs = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', infobox.group(1))

    # Filter out icons and affinity images
    card_imgs = [i for i in imgs if not any(p in i for p in ICON_PATTERNS)]
    if not card_imgs:
        return None

    # Prefer scaled images (they're definitely card images, not random infobox elements)
    scaled = [i for i in card_imgs if "scale-to-width" in i]
    url = scaled[0] if scaled else card_imgs[0]

    # Convert to full resolution by removing scale parameter
    url = re.sub(r"/scale-to-width-down/\d+", "", url)

    return url


def download_image(url: str, dest: Path) -> bool:
    """Download an image from a URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def get_extension(url: str) -> str:
    """Extract file extension from image URL."""
    match = re.search(r"\.(\w{3,4})/revision", url)
    if match:
        return f".{match.group(1).lower()}"
    return ".png"


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== Downloading Card Images ===")
    print(f"HTML source: {HTML_DIR}")
    print(f"Image dest:  {IMAGES_DIR}")
    print(f"Database:    {DB_PATH}\n")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")

    # Get all gear items with their URLs
    rows = conn.execute("SELECT id, name, url FROM gear").fetchall()
    gear_by_url = {r[2]: {"id": r[0], "name": r[1]} for r in rows if r[2]}

    # Build URL -> HTML file mapping
    html_files = {f.stem: f for f in HTML_DIR.glob("*.html") if f.stem != "_gear_index"}

    total = len(rows)
    downloaded = 0
    skipped = 0
    already_have = 0
    no_image = 0
    failed = []

    for i, (gear_id, name, url) in enumerate(rows, 1):
        pct = i * 100 // total

        # Find the HTML file for this item
        if url:
            wiki_slug = url.split("/wiki/")[-1] if "/wiki/" in url else ""
            wiki_slug = wiki_slug.replace("%27", "'").replace("%26", "&").replace("%28", "(").replace("%29", ")")
            wiki_slug = re.sub(r'[<>:"/\\|?*]', '_', wiki_slug)
        else:
            wiki_slug = name.replace(" ", "_")

        html_file = html_files.get(wiki_slug)
        if not html_file:
            print(f"[{i}/{total}] ({pct}%) SKIP (no HTML): {name}")
            skipped += 1
            continue

        # Determine output filename
        file_slug = slug_from_url(url) if url else name.lower().replace(" ", "_")

        # Check if we already have an image
        existing = list(IMAGES_DIR.glob(f"{file_slug}.*"))
        if existing:
            # Update DB if needed
            rel_path = existing[0].name
            conn.execute(
                "UPDATE gear SET image_path = ? WHERE id = ?",
                (rel_path, gear_id),
            )
            already_have += 1
            continue

        # Extract image URL from HTML
        html = html_file.read_text(encoding="utf-8")
        image_url = extract_image_url(html)

        if not image_url:
            print(f"[{i}/{total}] ({pct}%) NO IMAGE: {name}")
            no_image += 1
            continue

        ext = get_extension(image_url)
        dest = IMAGES_DIR / f"{file_slug}{ext}"

        print(f"[{i}/{total}] ({pct}%) Downloading: {name}...", end=" ", flush=True)

        if download_image(image_url, dest):
            conn.execute(
                "UPDATE gear SET image_url = ?, image_path = ? WHERE id = ?",
                (image_url, dest.name, gear_id),
            )
            conn.commit()
            downloaded += 1
            print("OK")
        else:
            failed.append(name)
            print("FAILED")

        time.sleep(REQUEST_DELAY)

    conn.commit()
    conn.close()

    print(f"\n=== Summary ===")
    print(f"Downloaded:    {downloaded}")
    print(f"Already had:   {already_have}")
    print(f"No HTML file:  {skipped}")
    print(f"No image found:{no_image}")
    print(f"Failed:        {len(failed)}")
    if failed:
        print("Failed items:")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
