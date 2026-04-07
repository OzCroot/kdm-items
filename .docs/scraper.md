# Scraper

## Overview

The scraper is a pure Python application (stdlib only, no third-party dependencies) that fetches gear data from the [KDM Fandom Wiki](https://kingdomdeath.fandom.com/wiki/Gear) and stores it in a SQLite database.

It runs as a single pipeline via `python run.py`, executing 8 stages in sequence. All wiki fetching is cached to disk so re-runs are fast.

## Pipeline Stages

| Stage | Module | Description |
|-------|--------|-------------|
| 1 | `fetch_index.py` | Fetch and parse the gear index page to get all item URLs |
| 2 | `fetch_pages.py` | Download gear HTML pages to `cache/gear/` |
| 3 | `fetch_pages.py` | Download definition HTML pages to `cache/definitions/` |
| 4 | `run.py` | Create database from `schema.sql` |
| 5 | `parse_gear.py` | Parse cached gear HTML into database |
| 6 | `parse_definitions.py` | Parse cached definition HTML into database |
| 7 | `fetch_images.py` | Download card images to `data/images/cards/` |
| 8 | `fetch_images.py` | Download icon images to `data/images/icons/` |

## Design Patterns

### Cache-First Architecture

All network requests write raw HTML to the `cache/` directory before any parsing happens. Parsing modules only read from cache, never from the network.

```
cache/
  gear/
    _index.html          # Gear index page
    Beacon_Shield.html   # One per gear item (named by URL slug)
    ...
  definitions/
    keywords/
      _category.html     # Category index page
      Melee.html         # One per definition page
      ...
    special_rules/
    settlement_locations/
```

This pattern means:
- **Re-running is fast** — cached pages are skipped automatically
- **Parser fixes don't require re-downloading** — use `--skip-download` to re-parse from cache
- **Full rebuild is easy** — use `--fresh-db` to recreate the database from existing cache

### Schema-as-Code

The complete database schema lives in a single `schema.sql` file. It is executed once to create a fresh database — no migrations, no ALTER TABLE, no schema split across multiple files.

When the schema needs to change:
1. Edit `schema.sql`
2. Run `python run.py --fresh-db` (deletes and recreates the database)

### Rate Limiting

Request delay is configurable via `--delay` CLI flag or `SCRAPER_DELAY` environment variable (default: 1.0s). On HTTP 403/429/5xx, requests are retried with exponential backoff (delay × 2^attempt, capped at 30s). Maximum retries configurable via `--max-retries` (default: 3).

## How Parsing Works

### Gear Index Parsing (`fetch_index.py`)

`parse_gear_index()` reads the main Gear wiki page and extracts item links from the heading structure:

- `<h2>` / `<h3>` headings → **expansion** names (if contains "Expansion" or is "Core Game")
- `<h3>` / `<h4>` headings → **category** (typically crafting location)
- Links within each section → individual gear items

A skip-list filters out non-gear pages (game concepts, mechanics). Output: `[{name, url, expansion, category}]`.

### Gear Page Parsing (`parse_gear.py`)

`parse_gear_page()` extracts data from two parts of each wiki page:

**Portable infobox** (`<aside class="portable-infobox">`) — structured data:
- Weapon stats: speed, accuracy, strength (from `<td data-source="X">`)
- Armor stats: hit_location, armor_rating (from `<div data-source="X">`)
- Keywords, special rule names, gained-by info

**Page body** — less structured:
- Card text (from `#Card_Text` section, with icon images converted to `[tag]` tokens)
- Crafting location (from prose: "may be crafted once the ___ settlement location...")
- Crafting cost (from `#Cost` section, parsed as `Nx Resource` lines)

### Type Classification

Gear type is inferred from parsed data:
- Has `speed` stat → `weapon`
- Has `armor_rating` or keyword `armor` → `armor`
- Has keyword `item` or `consumable` → `item`
- Otherwise → `other`

### Definition Parsing (`parse_definitions.py`)

Definitions for keywords, special rules, and settlement locations are scraped from wiki category pages. Each definition page's intro text (before the first `<h2>`) is extracted.

Title matching handles wiki disambiguation:
- Direct match, then stripped parentheticals (e.g. "Sharp (Keyword)" → "Sharp")
- "X" placeholder expansion (e.g. "Block X" matches "Block 1", "Block 2")
- Case-insensitive fallback

### Database Insert

`_insert_gear()` uses a DELETE + INSERT pattern instead of UPDATE. With `ON DELETE CASCADE` on junction tables, deleting a gear row automatically cleans up keywords, special rules, and crafting costs. This avoids stale data from partial updates.

The "weapon. melee" keyword bug (a single keyword that should be two) is fixed during insert by splitting on ". ".

## Module Dependencies

```
config ←── net ←── fetch_index
  ↑          ↑←── fetch_pages
  ↑          ↑←── fetch_images
utils ←── parse_gear
  ↑   ←── parse_definitions
  ↑   ←── fetch_index
  ↑   ←── fetch_images
```

Leaf modules (`config`, `utils`) have no internal dependencies. `net` depends only on `config`. All other modules import from these three.

## What It Captures

- Weapon stats (speed, accuracy, strength) — all weapons have complete stats
- Armor stats (hit_location, armor_rating) — all armor items populated
- Keywords — 74+ distinct keywords across 376 items
- Card text — 367+ items with parsed card text and icon tokens
- Crafting costs — 219+ items with recipe data
- Special rules — normalized into a junction table
- Definitions — keyword, special rule, and settlement location definitions from wiki
- Card images — downloaded to `data/images/cards/`
- Icon images — downloaded to `data/images/icons/`
- Expansion/category classification

## Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| **Affinities** | High | Affinity edge colors (top/bottom/left/right) are not parsed from the wiki. Schema columns exist but are not populated by the scraper. Needs manual curation or a parser improvement. |
| **Affinity bonuses** | Medium | Conditional affinity text is captured in `card_text` but not parsed into structured data. |
| **Type classification** | Low | A few items may be typed `other` that need manual review. |
