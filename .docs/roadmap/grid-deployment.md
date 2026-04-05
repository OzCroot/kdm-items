# Grid App Deployment

**Priority:** High
**Goal:** Automate building and deploying the gear grid SPA to GitHub Pages via CI/CD.
**Prerequisite:** Grid app is functional (Phase 2.3 complete)

## Overview

The grid app is a standalone Vue/Vite SPA that can be deployed independently of the main web editor. It loads `gear-data.json` and `images/` as static files at runtime — no backend needed.

**Pattern:** Private source repo (`kdm-items`) → GitHub Actions builds on tag push → pushes minified assets to public repo (`OzCroot/kdm-gear-grid`) → GitHub Pages serves at `ozcroot.github.io/kdm-gear-grid/`.

## Milestones

### G.1 — Base URL Configuration

Make asset paths work under a GitHub Pages subpath (`/kdm-gear-grid/`).

- Add `grid/.env.production` with `VITE_BASE_URL=/kdm-gear-grid/`
- Update `grid/vite.config.ts` to read base from env via `loadEnv`
- Prefix runtime data paths (`gear-data.json`, `images/`) with `import.meta.env.BASE_URL` in `App.vue`, `GridCell.vue`, `GearSearch.vue`
- Dev stays at `/` (no `.env` override), prod builds use `/kdm-gear-grid/`

### G.2 — GitHub Actions Workflow

Create `.github/workflows/deploy-grid.yml`:

- Trigger: tag push matching `grid-v*` (e.g., `git tag grid-v1.0.0 && git push origin grid-v1.0.0`)
- Steps: checkout → Node 22 setup → `npm ci` → `npm run build` in `grid/`
- Clone deployment repo using PAT (`DEPLOY_PAT` secret)
- Replace only app build artifacts (`index.html`, `assets/`) — preserve data files
- Commit and push to deployment repo

### G.3 — Deployment Repo Setup

One-time manual steps:

- [ ] Create public repo `OzCroot/kdm-gear-grid` (empty)
- [ ] Generate fine-grained PAT scoped to `kdm-gear-grid` (`Contents: Read and write`)
- [ ] Add PAT as `DEPLOY_PAT` secret in `kdm-items` repo settings
- [ ] Enable GitHub Pages on `kdm-gear-grid` (source: master branch, root)
- [ ] Seed deployment repo with `gear-data.json` and `images/` from a local scraper run

### G.4 — Data Management

Data files (`gear-data.json` + `images/`) live in the deployment repo only. App deploys preserve them.

- Initial data: run scraper locally, push output to `kdm-gear-grid`
- Data updates: push new data to `kdm-gear-grid` directly
- Future: optional "update data" workflow to automate scraper → deploy repo

## Done When

- Pushing a `grid-v*` tag triggers a build and deploys to GitHub Pages
- `ozcroot.github.io/kdm-gear-grid/` serves the grid app with gear data and images
- No local checkout of the deployment repo is needed
- Data can be updated independently of app code
