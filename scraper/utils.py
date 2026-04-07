"""Shared parsing utilities for the KDM gear scraper."""

import re
from html import unescape

ICON_TAG_MAP = {
    "Activation": "activation",
    "Movement": "movement",
    "Reaction": "reaction",
    "Blue Affinity Icon": "blue_affinity",
    "Red Affinity Box": "red_affinity",
    "Green Affinity Box": "green_affinity",
    "Blue Puzzle Affinity": "blue_puzzle",
    "Red Puzzle Affinity": "red_puzzle",
    "Green Puzzle Affinity": "green_puzzle",
    "AI Card Icon": "ai_card",
    "Monster Level": "monster_level",
    "Pumpkin": "pumpkin",
}


def clean_html(text: str) -> str:
    """Strip HTML tags, normalize whitespace."""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n ", "\n", text)
    return text.strip()


def parse_card_text(html: str) -> str:
    """Convert icon images to [tag] tokens, strip HTML, normalize paragraphs."""

    def replace_icon(m: re.Match) -> str:
        alt = m.group(1)
        tag = ICON_TAG_MAP.get(alt)
        return f"[{tag}]" if tag else ""

    text = re.sub(r'<img[^>]*alt="([^"]+)"[^>]*/?\s*>', replace_icon, html)
    text = re.sub(
        r'<span[^>]*class="mobile-workaround-[^"]*"[^>]*>[^<]*</span>', "", text
    )
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    paragraphs = re.split(r"\n\n+", text)
    result = []
    for para in paragraphs:
        para = re.sub(r"\s+", " ", para).strip()
        if para:
            result.append(para)
    return "\n".join(result)


def slug_from_url(url: str) -> str:
    """Convert wiki URL to filesystem-safe slug (case-preserving)."""
    slug = url.split("/wiki/")[-1] if "/wiki/" in url else url
    slug = (
        slug.replace("%27", "'")
        .replace("%26", "&")
        .replace("%28", "(")
        .replace("%29", ")")
    )
    slug = re.sub(r'[<>:"/\\|?*]', "_", slug)
    return slug


def extract_icon_urls(html: str) -> dict[str, str]:
    """Extract icon image URLs from card text HTML."""
    urls: dict[str, str] = {}
    for match in re.finditer(
        r'<img[^>]*alt="([^"]+)"[^>]*src="([^"]+)"[^>]*/?\s*>', html
    ):
        alt, url = match.group(1), match.group(2)
        tag = ICON_TAG_MAP.get(alt)
        if tag and tag not in urls:
            url = re.sub(r"/scale-to-width-down/\d+", "", url)
            urls[tag] = url
    return urls
