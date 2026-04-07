# KDM Gear Scraper

Scrapes gear data from the [Kingdom Death: Monster Fandom wiki](https://kingdomdeath.fandom.com/wiki/Gear) into a SQLite database.

## Quick Start

```bash
cd scraper
python run.py
```

This runs all 8 pipeline stages end-to-end, skipping any downloads that are already cached.

## Pipeline Stages

| Stage | Module | What it does |
|-------|--------|-------------|
| 1 | `fetch_index.py` | Fetch the gear index page and parse all item URLs |
| 2 | `fetch_pages.py` | Download gear HTML pages to `cache/gear/` |
| 3 | `fetch_pages.py` | Download definition HTML pages to `cache/definitions/` |
| 4 | `run.py` | Create database from `schema.sql` |
| 5 | `parse_gear.py` | Parse cached HTML into gear tables |
| 6 | `parse_definitions.py` | Parse cached HTML into definition tables |
| 7 | `fetch_images.py` | Download card images to `data/images/cards/` |
| 8 | `fetch_images.py` | Download icon images to `data/images/icons/` |

## CLI Options

```
python run.py                     # Run everything, skip cached
python run.py --delay 2.0         # Custom request delay (env: SCRAPER_DELAY)
python run.py --fresh-db           # Delete and recreate database
python run.py --skip-download      # Parse from existing cache only
python run.py --skip-images        # Skip image download stages
python run.py -v                   # Verbose/debug logging
```

## Architecture

### Cache-First Design

All wiki fetching writes raw HTML to `cache/` before any parsing happens. Parsing only reads from cache. This means:
- Re-running the pipeline is fast (network requests are skipped)
- Parser bugs can be fixed and re-run without re-downloading
- `--skip-download` lets you parse from cache only
- `--fresh-db` recreates the database from cached data

### Schema-as-Code

The complete database schema lives in `schema.sql` — a single SQL file executed once to create a fresh database. No migrations, no ALTER TABLE. When the schema changes, delete the database and re-run.

### Configurable Rate Limiting

Request delay is configurable via `--delay` or the `SCRAPER_DELAY` environment variable (default: 1.0s). Failed requests are retried with exponential backoff up to 30s, configurable with `--max-retries` (default: 3).

## File Structure

```
scraper/
  run.py                 # Entry point
  schema.sql             # Database schema (single source of truth)
  config.py              # Paths, URLs, constants, CLI args
  net.py                 # HTTP fetch with retry/backoff
  utils.py               # Shared parsing utilities
  fetch_index.py         # Stage 1
  fetch_pages.py         # Stages 2-3
  parse_gear.py          # Stage 5
  parse_definitions.py   # Stage 6
  fetch_images.py        # Stages 7-8
  export_json.py         # Standalone JSON export (not part of pipeline)
  cache/
    gear/                # Cached gear page HTML
    definitions/
      keywords/          # Cached keyword definition pages
      special_rules/     # Cached special rule definition pages
      settlement_locations/
```

## JSON Export

`export_json.py` is separate from the pipeline. It exports the database to `grid/public/gear-data.json` for the standalone gear grid app:

```bash
python export_json.py
```

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

All modules use stdlib only — no pip dependencies required.
