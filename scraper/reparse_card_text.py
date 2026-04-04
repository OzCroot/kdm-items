"""
Re-parse card_text and crafting_costs from cached HTML files.
Updates ONLY those two fields in the DB. Also extracts icon image URLs
and downloads icon images.
"""

import os
import re
import json
import sqlite3
import urllib.request
from html import unescape
from pathlib import Path

import scraper

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "kdm_gear.db"))
HTML_DIR = Path(os.environ.get("HTML_DIR", Path(__file__).parent / "html_pages"))
ICONS_DIR = Path(os.environ.get("ICONS_DIR", Path(__file__).parent.parent / "data" / "images" / "icons"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://kingdomdeath.fandom.com"

# Reverse map: tag name -> wiki alt text for icon URL extraction
TAG_TO_ALT = {v: k for k, v in scraper.ICON_TAG_MAP.items()}


def extract_icon_urls(html: str) -> dict[str, str]:
    """Extract icon image URLs from card text HTML section."""
    urls: dict[str, str] = {}
    for match in re.finditer(r'<img[^>]*alt="([^"]+)"[^>]*src="([^"]+)"[^>]*/?\s*>', html):
        alt, url = match.group(1), match.group(2)
        tag = scraper.ICON_TAG_MAP.get(alt)
        if tag and tag not in urls:
            # Get full resolution URL
            url = re.sub(r"/scale-to-width-down/\d+", "", url)
            urls[tag] = url
    return urls


def parse_card_text_section(content: str) -> tuple[str, str]:
    """Extract raw card text HTML section and parse it. Returns (parsed_text, raw_html)."""
    match = re.search(
        r'id="Card_Text".*?</h\d>(.*?)(?=<h\d|<!--\s*NewPP|<div\s+class="printfooter|<div\s+id="catlinks)',
        content,
        re.DOTALL,
    )
    if not match:
        return "", ""
    raw = match.group(1)
    return scraper.parse_card_text(raw), raw


def parse_crafting_costs(content: str) -> list[dict]:
    """Extract crafting costs with fixed boundary."""
    cost_match = re.search(
        r'id="Cost".*?</h\d>(.*?)(?=<h\d|<!--\s*NewPP|<div\s+class="printfooter|<div\s+id="catlinks)',
        content,
        re.DOTALL,
    )
    if not cost_match:
        return []

    cost_text = scraper.clean_html(cost_match.group(1)).strip()
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
    return cost_items


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Database: {DB_PATH}")
    print(f"HTML source: {HTML_DIR}")
    print(f"Icons dest: {ICONS_DIR}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON")

    # Get all gear items with URLs for matching
    rows = conn.execute("SELECT id, name, url FROM gear").fetchall()
    url_to_id = {}
    for gid, name, url in rows:
        if url:
            slug = url.split("/wiki/")[-1] if "/wiki/" in url else ""
            slug = slug.replace("%27", "'").replace("%26", "&").replace("%28", "(").replace("%29", ")")
            slug = re.sub(r'[<>:"/\\|?*]', '_', slug)
            url_to_id[slug] = (gid, name)

    # Collect all icon URLs across items
    all_icon_urls: dict[str, str] = {}
    updated_text = 0
    updated_costs = 0

    html_files = sorted(HTML_DIR.glob("*.html"))
    html_files = [f for f in html_files if f.stem != "_gear_index"]
    total = len(html_files)

    for i, filepath in enumerate(html_files, 1):
        slug = filepath.stem
        match = url_to_id.get(slug)
        if not match:
            continue
        gear_id, name = match

        html = filepath.read_text(encoding="utf-8")
        idx = html.find("mw-parser-output")
        if idx == -1:
            continue
        content = html[idx: idx + 60000]

        # Parse card text
        card_text, raw_html = parse_card_text_section(content)
        if card_text:
            conn.execute("UPDATE gear SET card_text = ? WHERE id = ?", (card_text, gear_id))
            updated_text += 1

            # Extract icon URLs from raw HTML
            icons = extract_icon_urls(raw_html)
            all_icon_urls.update(icons)

        # Parse crafting costs
        costs = parse_crafting_costs(content)
        # Clear and re-insert costs
        conn.execute("DELETE FROM crafting_costs WHERE gear_id = ?", (gear_id,))
        for cost in costs:
            conn.execute(
                "INSERT INTO crafting_costs (gear_id, resource, quantity) VALUES (?, ?, ?)",
                (gear_id, cost["resource"], cost["quantity"]),
            )
        if costs:
            updated_costs += 1

        if i % 50 == 0:
            print(f"  [{i}/{total}] processed...")

    conn.commit()
    print(f"\nUpdated card_text: {updated_text} items")
    print(f"Updated crafting_costs: {updated_costs} items")

    # Update icon URLs in card_text_icons table
    print(f"\n=== Icon URLs found: {len(all_icon_urls)} ===")
    for tag, url in sorted(all_icon_urls.items()):
        conn.execute("UPDATE card_text_icons SET icon_url = ? WHERE tag = ?", (url, tag))
        print(f"  {tag}: {url[:80]}...")
    conn.commit()

    # Download icon images
    print(f"\n=== Downloading icon images ===")
    downloaded = 0
    for tag, url in sorted(all_icon_urls.items()):
        ext = ".png"
        ext_match = re.search(r"\.(\w{3,4})/revision", url)
        if ext_match:
            ext = f".{ext_match.group(1).lower()}"
        dest = ICONS_DIR / f"{tag}{ext}"
        if dest.exists():
            print(f"  {tag}: already exists")
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            downloaded += 1
            print(f"  {tag}: OK")
        except Exception as e:
            print(f"  {tag}: FAILED ({e})")

    conn.close()
    print(f"\nDownloaded {downloaded} icon images to {ICONS_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
