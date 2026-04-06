# KDM Items

A gear database for [Kingdom Death: Monster](https://kingdomdeath.fandom.com/wiki/Kingdom_Death:_Monster), scraped from the Fandom wiki. Browse, search, and curate gear data through a web UI backed by a REST API and SQLite database.

**Gear Grid Builder:** [ozcroot.github.io/kdm-gear-grid](https://ozcroot.github.io/kdm-gear-grid/)

## Projects

- **scraper/** — Python scripts that scrape gear data from the Fandom wiki into a SQLite database. Handles gear items, keyword/rule definitions, and card images.
- **api/** — Express + TypeScript REST API serving gear data from SQLite. Supports filtering, search, CRUD operations, and image serving.
- **web/** — Vue 3 + TailwindCSS frontend for browsing and editing the gear database. Features sortable columns, inline editing, and card image previews.
- **grid/** — Standalone gear grid builder app deployed to GitHub Pages. Lets you lay out gear cards on a grid with drag-and-drop and affinity link visualization.

All services share a SQLite database (`kdm_gear.db`) via a Docker volume.

## Quick Start (Docker)

```bash
# Start the API and web UI
docker compose up

# Web UI: http://localhost:5173
# API:    http://localhost:3000
```

To run the scraper (populates the database):

```bash
docker compose --profile scraper up scraper
```

## Local Development

### Prerequisites

- Python 3.13+ (scraper — stdlib only, no pip install needed)
- Node.js 24+ (api, web, grid)

### Scraper

```bash
cd scraper
python scraper.py              # Scrape gear data from wiki
python scrape_definitions.py   # Scrape keyword/rule definitions
python download_images.py      # Download card images
```

The database is written to `data/kdm_gear.db` by default. Override with `DB_PATH` env var.

### API

```bash
cd api
npm install
npm run dev       # Dev server with auto-reload on :3000
```

Set `DB_PATH` to point at your database file (defaults to `../data/kdm_gear.db`).

### Web

```bash
cd web
npm install
npm run dev       # Vite dev server with HMR on :5173
```

### Grid

```bash
cd grid
npm install
npm run dev       # Vite dev server
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/gear` | List gear (supports `?type=`, `?expansion=`, `?keyword=`, `?search=`) |
| GET | `/api/gear/:id` | Get a single item with keywords and crafting costs |
| PUT | `/api/gear/:id` | Update an item |
| POST | `/api/gear` | Create an item |
| DELETE | `/api/gear/:id` | Delete an item |
| GET | `/api/keywords` | List all keywords |
| GET | `/api/images/:filename` | Serve a card image |
| GET | `/api/health` | Health check |
