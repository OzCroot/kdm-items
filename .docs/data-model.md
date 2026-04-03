# Data Model

## Database

SQLite database: `data/kdm_gear.db`

## Current Schema

### `gear`

The main table. One row per gear item.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `name` | TEXT NOT NULL UNIQUE | Gear item name |
| `type` | TEXT | `weapon`, `armor`, `item`, or `other` |
| `expansion` | TEXT | Which expansion the gear belongs to |
| `category` | TEXT | Crafting location or sub-category from the wiki |
| `url` | TEXT | Source wiki URL |
| `speed` | TEXT | Weapon stat: number of attack dice |
| `accuracy` | TEXT | Weapon stat: minimum roll to hit (e.g., "6+") |
| `strength` | TEXT | Weapon stat: added to wound rolls |
| `hit_location` | TEXT | Armor: which body part it protects (Head/Arms/Body/Waist/Legs) |
| `armor_rating` | TEXT | Armor: damage absorption value |
| `gained_by` | TEXT | How the item is obtained (if not crafted) |
| `card_text` | TEXT | Full rules text from the card |
| `crafting_location` | TEXT | Settlement location where it's crafted |
| `special_rules_names` | TEXT | JSON array of special rule names |
| `raw_json` | TEXT | Full scraped data as JSON backup |

### `gear_keywords`

Join table: each gear item can have multiple keywords.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `gear_id` | INTEGER FK | References `gear.id` |
| `keyword` | TEXT NOT NULL | A single keyword (e.g., "melee", "heavy") |

### `crafting_costs`

Join table: each gear item can require multiple resources to craft.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-incrementing ID |
| `gear_id` | INTEGER FK | References `gear.id` |
| `resource` | TEXT NOT NULL | Resource name (e.g., "Iron", "Bone") |
| `quantity` | INTEGER NOT NULL | How many are needed (default: 1) |

## Current Data Summary

- **376 total items** across 13 expansions
- **127 weapons**, **77 armor**, **135 items**, **5 other**
- **219 items** have crafting costs
- **367 items** have card text
- **104 items** have `gained_by` data
- **74 distinct keywords**

### Expansion Breakdown

| Expansion | Count |
|-----------|-------|
| Core Game | 136 |
| Gambler's Chest | 99 |
| Sunstalker | 23 |
| Dragon King | 20 |
| Gorm | 20 |
| Dung Beetle Knight | 17 |
| Spidicules | 17 |
| Slenderman | 10 |
| Flower Knight | 9 |
| Lion God | 9 |
| Green Knight | 7 |
| Manhunter | 5 |
| Lion Knight | 4 |

## What "Correct" Looks Like

### Weapons
- Must have `speed`, `accuracy`, `strength` (all populated)
- `accuracy` should follow the format `N+` (e.g., "6+", "8+")
- Must have keyword `weapon` and at least one of: `melee`, `ranged`, `thrown`
- `type` = `weapon`

### Armor
- Must have `hit_location` (one of: Head, Arms, Body, Waist, Legs)
- Must have `armor_rating` (numeric, typically 0-6)
- Must have keyword `armor`
- `type` = `armor`

### Items
- Non-weapon, non-armor gear (consumables, tools, jewelry, etc.)
- Should have keyword `item`, `consumable`, or similar
- `type` = `item`

### All Gear
- Should have affinities (top, bottom, left, right — each is a color or none)
- Should have a card image stored locally
- If craftable, should have `crafting_location` and entries in `crafting_costs`
- If not craftable (rare gear), should have `gained_by`

## Known Data Gaps

### Missing: Affinities
The scraper has partial code to detect affinities but **does not store them**. Affinities are critical for gear grid strategy and must be added. This requires:
- New columns or a new table for affinity data (top, bottom, left, right colors)
- Scraper update to extract affinity info from the infobox
- Possible manual curation since wiki markup for affinities is inconsistent

### Missing: Card Images
Card images exist on the wiki but are not scraped or stored. Planned approach:
- Extract image URLs from cached HTML pages
- Download and store locally in `data/images/` with lowercase slug filenames (e.g., `beacon_shield.png`)
- Add `image_url` (source) and `image_path` (local file) columns to `gear`

### Data Error: `weapon. melee` Keyword
The item "Plated Shield (Gear)" has the keyword `weapon. melee` (with a period and space) instead of separate `weapon` and `melee` keywords. This is a scraper parsing bug.

### Miscategorized: "other" Type Items
Only 1 item is currently typed `other`:
- **Lovelorn Rock** (Gambler's Chest, Rare Gear) — has no type-identifying keywords

Some items typed `other` may need manual review and reclassification.

### 32 Items Required Manual Retry
The initial scrape failed on 32 items (403 errors / timeouts). These were hardcoded in `download_pages.py` as `FAILED_ITEMS` and retried separately. All are now in the DB but may have been parsed from a different page state.

## Planned Schema Changes

### Version Support
Some gear cards have been errata'd or reprinted with different stats across KDM editions. To support multiple versions:

- Add `version` TEXT column to `gear` (e.g., "1.0", "1.5", "1.6", "errata")
- Change unique constraint from `UNIQUE(name)` to `UNIQUE(name, version)`
- Default existing items to version "1.5" (most common source on the wiki)

### Image Storage
- Add `image_url` TEXT column — original wiki image URL
- Add `image_path` TEXT column — local path relative to `data/images/`

### Affinity Storage
- Add `affinity_top` TEXT column (red/green/blue/none)
- Add `affinity_bottom` TEXT column
- Add `affinity_left` TEXT column
- Add `affinity_right` TEXT column

Or alternatively, a separate `gear_affinities` table if affinities turn out to be more complex (e.g., paired affinities, conditional affinities).
