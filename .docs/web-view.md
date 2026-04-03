# Web View

## Purpose

A web application for browsing, viewing, and editing KDM gear data. The primary use case is **data curation** — reviewing scraped data and correcting errors with the actual card image as a visual reference.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + TypeScript |
| Build | Vite |
| API | Node.js + Express + TypeScript |
| Database | SQLite via `better-sqlite3` |
| Infrastructure | Docker Compose (all services containerized) |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vue 3     │────>│  Express    │────>│   SQLite    │
│  Frontend   │     │  API        │     │   (data/)   │
│  (web/)     │     │  (api/)     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
     :5173               :3000           kdm_gear.db
                          │               images/
                          │
                    Serves images
                    from data/images/
```

All three services run as Docker containers with a shared volume for `data/`.

## Layout

### List View

Browse all gear with filtering and search.

```
┌──────────────────────────────────────────────────┐
│  Search: [_______________]                       │
│  Type: [All|Weapon|Armor|Item]  Expansion: [__]  │
│  Keyword: [__]  Show: [Issues only]              │
├──────────────────────────────────────────────────┤
│  Name              Type    Expansion     Issues   │
│  ─────────────────────────────────────────────── │
│  Beacon Shield     weapon  Core Game     -        │
│  Lantern Cuirass   armor   Core Game     -        │
│  Almanac           item    Core Game     -        │
│  Lovelorn Rock     other   Gambler's     type?    │
│  ...                                              │
└──────────────────────────────────────────────────┘
```

Key features:
- Filter by type, expansion, keyword
- "Issues only" filter to surface items with data gaps (missing affinities, missing images, suspicious types)
- Sort by any column
- Pagination or virtual scroll

### Detail/Edit View

Card image alongside an editable form.

```
┌──────────────────────────────────────────────────┐
│  < Back to list                     [Save] [Next]│
├───────────────────┬──────────────────────────────┤
│                   │  Name: [Beacon Shield    ]   │
│                   │  Type: [weapon ▼]            │
│   ┌───────────┐   │  Expansion: [Core Game ▼]    │
│   │           │   │  Category: [Blacksmith   ]   │
│   │  Card     │   │                              │
│   │  Image    │   │  -- Weapon Stats --           │
│   │           │   │  Speed: [1  ]                │
│   │           │   │  Accuracy: [6+ ]             │
│   │           │   │  Strength: [5  ]             │
│   └───────────┘   │                              │
│                   │  -- Keywords --               │
│                   │  [weapon] [melee] [shield]    │
│                   │  [metal] [heavy] [+Add]       │
│                   │                              │
│                   │  -- Card Text --              │
│                   │  [________________________]  │
│                   │  [________________________]  │
│                   │                              │
│                   │  -- Crafting Cost --          │
│                   │  2x Iron  1x Bone  [+Add]    │
│                   │                              │
│                   │  -- Affinities --             │
│                   │  Top: [blue ▼]               │
│                   │  Right: [red ▼]              │
│                   │  Bottom: [none ▼]            │
│                   │  Left: [none ▼]              │
│                   │                              │
│                   │  Version: [1.5       ]       │
├───────────────────┴──────────────────────────────┤
│  < Prev                                   Next > │
└──────────────────────────────────────────────────┘
```

Key features:
- Card image displayed on the left as visual reference
- All fields editable
- Keywords as tags with add/remove
- Crafting costs as editable list
- Affinity dropdowns (red/green/blue/none for each edge)
- Version field for errata/reprints
- Prev/Next navigation to move through the list without going back
- Save button persists changes immediately

## Validation

Light validation with **warnings, not blockers**. Some items intentionally break the rules (special gear, promo items, etc.).

| Rule | Severity | Description |
|------|----------|-------------|
| Weapon missing stats | Warning | Weapons should have speed, accuracy, strength |
| Armor missing hit_location | Warning | Armor should specify a body location |
| Armor missing armor_rating | Warning | Armor should have a numeric rating |
| Unknown type | Warning | Items typed "other" may need review |
| Missing image | Info | Item has no card image stored locally |
| Missing affinities | Info | Affinities not yet populated |

Warnings display as inline indicators on the form, not as modal dialogs or submit blockers.

## API Endpoints

### Gear

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/gear` | List all gear (supports `?type=`, `?expansion=`, `?keyword=`, `?search=`, `?issues=true`) |
| GET | `/api/gear/:id` | Get a single gear item with all related data |
| PUT | `/api/gear/:id` | Update a gear item |
| POST | `/api/gear` | Create a new gear item (for manual additions or version duplicates) |
| DELETE | `/api/gear/:id` | Delete a gear item |

### Keywords

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/keywords` | List all distinct keywords |

### Images

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/images/:filename` | Serve a card image from `data/images/` |

## Docker Setup

```yaml
# docker-compose.yml (web-related services)

services:
  api:
    build: ./api
    ports:
      - "3000:3000"
    volumes:
      - kdm-data:/app/data
    environment:
      - DB_PATH=/app/data/kdm_gear.db
      - IMAGES_PATH=/app/data/images

  web:
    build: ./web
    ports:
      - "5173:5173"
    volumes:
      - ./web/src:/app/src  # HMR during dev
    depends_on:
      - api

volumes:
  kdm-data:
```
