# KDM Items

A data project for **Kingdom Death: Monster** gear items. Scrapes the KDM Fandom wiki, stores structured gear data in SQLite, and provides a web interface for browsing, curating, and editing the dataset.

## Vision

The project has three phases, in priority order:

1. **Curate** — The scraped data is a strong starting point (376 items) but has gaps. Build a web editor to review and correct items, add missing data (affinities, images), and handle errata/reprints as versioned entries.
2. **Reference** — Once the data is clean, provide a polished searchable/filterable gear database for use during KDM game sessions.
3. **Community** — Share the tool publicly so other KDM players can use and contribute to the dataset.

## Architecture

```
kdm-items/
├── .docs/              # Project documentation
├── scraper/            # Python scraper (Dockerized)
├── api/                # Node.js + Express + TypeScript API
├── web/                # Vue 3 + TypeScript frontend
├── data/               # Shared Docker volume (DB + images)
└── docker-compose.yml  # Orchestrates all services
```

All services run in Docker containers via `docker-compose up`. The `data/` directory is a shared Docker volume containing the SQLite database and locally-stored card images.

## KDM Glossary

Key domain concepts referenced throughout the docs:

| Term | Definition |
|------|-----------|
| **Gear** | Equipment cards that survivors can carry. Each survivor has a 3x3 gear grid. |
| **Gear Grid** | A 3x3 grid of slots on a survivor sheet. Gear placement matters because of affinity connections. |
| **Affinities** | Colored connections (red, green, blue) on the four edges of a gear card (top, bottom, left, right). When adjacent gear cards share matching affinity colors on touching edges, affinity bonuses can activate. |
| **Affinity Bonus** | A special ability on a gear card that activates when the required affinity conditions are met (e.g., "2 blue affinities: +1 strength"). |
| **Keywords** | Tags on gear cards (e.g., `weapon`, `melee`, `heavy`, `metal`, `bone`). Keywords interact with game rules, abilities, and crafting. |
| **Hit Location** | Where armor protects on the body: `Head`, `Arms`, `Body`, `Waist`, or `Legs`. Each armor piece covers one location. |
| **Armor Rating** | A numeric value (0-6 typically) indicating how much damage armor absorbs at its hit location. |
| **Weapon Stats** | Weapons have three stats: **Speed** (number of attack dice), **Accuracy** (minimum roll to hit, e.g., 6+), **Strength** (added to wound rolls). |
| **Expansion** | A content pack that adds new monsters, gear, and mechanics. Examples: Dragon King, Gorm, Sunstalker. The base game is "Core Game". |
| **Settlement Location** | A crafting station in the settlement (e.g., Blacksmith, Leather Worker, Stone Circle). Gear is crafted at specific locations. |
| **Crafting Cost** | Resources required to craft a gear item (e.g., "2x Iron, 1x Leather"). |
| **Special Rules** | Unique abilities or effects printed on a gear card beyond its base stats. |
| **Rare Gear** | Gear that cannot be crafted and is obtained through special events or monster rewards. |
| **Card Text** | The full rules text printed on a gear card, including special rules and flavor text. |
| **Errata** | Official corrections to printed cards. Some gear has been reprinted with different stats or rules across editions. |
