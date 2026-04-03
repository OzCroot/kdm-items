# Scraper

## Overview

The scraper is a pure Python application (stdlib only, no third-party dependencies) that fetches gear data from the [KDM Fandom Wiki](https://kingdomdeath.fandom.com/wiki/Gear) and stores it in a SQLite database.

It consists of two scripts:
- `scraper.py` — Main scraper: parses the gear index, visits each item page, extracts data, writes to SQLite
- `download_pages.py` — Downloads raw HTML pages locally and re-parses them into the DB

## How It Works

### Step 1: Parse the Gear Index

`parse_gear_index()` fetches the main [Gear](https://kingdomdeath.fandom.com/wiki/Gear) wiki page and extracts all gear item links organized by heading structure:

- `<h2>` / `<h3>` headings map to **expansion** names
- `<h3>` / `<h4>` headings map to **category** (typically crafting location)
- Links within each section are the individual gear items

A skip-list filters out non-gear pages (game concepts, mechanics, etc.).

Output: a list of `{name, url, expansion, category}` dicts.

### Step 2: Parse Individual Gear Pages

`parse_gear_page()` visits each item's wiki page and extracts data from:

- **Portable infobox** (`<aside class="portable-infobox">`) — structured data:
  - Weapon stats: speed, accuracy, strength
  - Armor stats: hit_location, armor_rating
  - Keywords
  - Special rule names
  - Gained-by info
- **Page body** — less structured:
  - Card text (from `#Card_Text` section)
  - Crafting location (from prose like "may be crafted once the ___ settlement location...")
  - Crafting cost (from `#Cost` section, parsed as `Nx Resource` lines)

### Step 3: Type Classification

Gear type is inferred from the data, not from the wiki:
- Has `speed` stat → `weapon`
- Has `armor_rating` or keyword `armor` → `armor`
- Has keyword `item` or `consumable` → `item`
- Otherwise → `other`

### Step 4: Database Insert

`insert_gear()` upserts by name — updates existing records, inserts new ones. Related data (keywords, crafting costs) is cleared and re-inserted on update.

## Caching Strategy

### HTML Page Cache (`html_pages/`)

`download_pages.py` saves raw HTML for every gear page to `html_pages/`. Files are named using URL slugs (e.g., `Beacon_Shield.html`). Pages already on disk are skipped.

This serves two purposes:
1. Avoids re-fetching from the wiki on subsequent runs
2. Allows re-parsing with an improved parser without hitting the wiki again

### Failed Items List

32 items failed the initial scrape (HTTP 403 / timeouts). These are hardcoded as `FAILED_ITEMS` in `download_pages.py` and retried with longer delays (3s between requests).

## Rate Limiting

- `scraper.py`: 0.5s between requests
- `download_pages.py`: 1.5s between requests, 3s on retry pass
- User-Agent is set to a Chrome-like string to avoid basic bot blocking

## What It Captures Well

- Weapon stats (speed, accuracy, strength) — all 127 weapons have complete stats
- Armor stats (hit_location, armor_rating) — all 77 armor items are populated  
- Keywords — 74 distinct keywords across 376 items
- Card text — 367 of 376 items
- Crafting costs — 219 items have recipe data
- Expansion/category classification

## What It Captures Poorly or Not At All

| Gap | Severity | Notes |
|-----|----------|-------|
| **Affinities** | High | Code to detect them exists but never stores the result. Critical for gameplay. |
| **Card images** | High | Not extracted at all. Images exist on the wiki in the infobox. |
| **Keyword parsing edge cases** | Low | One item has `weapon. melee` as a single keyword instead of two separate keywords. |
| **Type classification** | Low | 1 item typed `other` that may need manual review. |
| **Affinity bonuses** | Medium | The conditional text for affinity bonuses is captured in `card_text` but not parsed into structured data. |

## Planned Enhancements

- **Image extraction**: Parse infobox for card image URLs, download to `data/images/` with lowercase slugs
- **Affinity extraction**: Parse the infobox affinity squares into structured top/bottom/left/right color data
- **Dockerize**: Move scraper into its own Docker container with a `Dockerfile`, outputting to a shared volume
