# Phase 1: Data Curation

**Priority:** Highest
**Goal:** Get the gear data to a state where every item is correct and complete.

## Milestones

### 1.1 — Repo Restructure

Move from flat layout to monorepo structure:

```
kdm-items/
├── .docs/
├── scraper/
│   ├── scraper.py
│   ├── download_pages.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── html_pages/
├── api/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
├── web/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
├── data/
│   ├── kdm_gear.db
│   └── images/
└── docker-compose.yml
```

### 1.2 — Dockerize the Scraper

- Create `scraper/Dockerfile` (Python base image)
- Mount `data/` as a shared Docker volume
- Scraper writes DB and images to the volume
- Test: `docker-compose run scraper` produces a populated DB

### 1.3 — Schema Migration

Apply planned schema changes:
- Add `version` column (default "1.5"), change unique constraint to `(name, version)`
- Add `image_url`, `image_path` columns
- Add affinity columns (`affinity_top`, `affinity_bottom`, `affinity_left`, `affinity_right`)
- Fix `weapon. melee` keyword bug

### 1.4 — Image Scraping

- Extract card image URLs from cached HTML pages (infobox `<img>` tags)
- Download images to `data/images/` with lowercase slug filenames
- Store `image_url` and `image_path` in the DB
- Test: spot-check 10+ items have correct images

### 1.5 — API Server

- Set up Node.js + Express + TypeScript project in `api/`
- Implement REST endpoints (see [web-view.md](../web-view.md#api-endpoints))
- Serve images from `data/images/`
- Dockerize with shared volume mount
- Test: `curl` all endpoints return expected data

### 1.6 — Web Editor (MVP)

- Set up Vue 3 + TypeScript + Vite project in `web/`
- List view with filtering (type, expansion, keyword, search)
- Detail/edit view with card image + form
- Save changes via API
- Prev/Next navigation
- Dockerize with Vite HMR
- Test: full edit round-trip (change a field, save, reload, verify)

### 1.7 — Data Curation Pass

With the editor in place, systematically review and fix:
- [ ] Items typed "other" — reclassify or confirm
- [ ] Missing affinities — populate from card images
- [ ] Missing `gained_by` on rare/non-craftable gear
- [ ] Verify weapon stats against card images
- [ ] Verify armor stats against card images
- [ ] Review items from the FAILED_ITEMS retry list

## Done When

- Every gear item has correct type, stats, keywords, and affinities
- Every item has a locally stored card image
- The web editor is functional for ongoing corrections
- All services run via `docker-compose up`
