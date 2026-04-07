-- KDM Gear Database Schema
-- Single source of truth — executed once to create a fresh database.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS versions (
    name TEXT PRIMARY KEY,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS expansions (
    name TEXT PRIMARY KEY,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS gear (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.5',
    type TEXT,
    expansion TEXT,
    category TEXT,
    url TEXT,

    -- Weapon stats
    speed TEXT,
    accuracy TEXT,
    strength TEXT,

    -- Armor stats
    hit_location TEXT,
    armor_rating TEXT,

    -- Affinities
    affinity_top TEXT,
    affinity_bottom TEXT,
    affinity_left TEXT,
    affinity_right TEXT,

    -- Content
    gained_by TEXT,
    card_text TEXT,
    crafting_location TEXT,

    -- Images
    image_url TEXT,
    image_path TEXT,

    -- Denormalized backup
    special_rules_names TEXT,
    raw_json TEXT,

    UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS gear_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gear_id INTEGER NOT NULL REFERENCES gear(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gear_special_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gear_id INTEGER NOT NULL REFERENCES gear(id) ON DELETE CASCADE,
    rule TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crafting_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gear_id INTEGER NOT NULL REFERENCES gear(id) ON DELETE CASCADE,
    resource TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS keyword_definitions (
    keyword TEXT PRIMARY KEY,
    definition TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS special_rule_definitions (
    rule TEXT PRIMARY KEY,
    definition TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS settlement_locations (
    name TEXT PRIMARY KEY,
    definition TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS card_text_icons (
    tag TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    icon_url TEXT NOT NULL DEFAULT '',
    icon_path TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_gear_name ON gear(name);
CREATE INDEX IF NOT EXISTS idx_gear_type ON gear(type);
CREATE INDEX IF NOT EXISTS idx_gear_expansion ON gear(expansion);
CREATE INDEX IF NOT EXISTS idx_gear_keywords_gear_id ON gear_keywords(gear_id);
CREATE INDEX IF NOT EXISTS idx_gear_keywords_keyword ON gear_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_gear_special_rules_gear_id ON gear_special_rules(gear_id);
CREATE INDEX IF NOT EXISTS idx_gear_special_rules_rule ON gear_special_rules(rule);
CREATE INDEX IF NOT EXISTS idx_crafting_costs_gear_id ON crafting_costs(gear_id);

-- Seed data: card text icons
INSERT OR IGNORE INTO card_text_icons (tag, display_name) VALUES
    ('activation', 'Activation'),
    ('movement', 'Movement'),
    ('reaction', 'Reaction'),
    ('blue_affinity', 'Blue Affinity'),
    ('red_affinity', 'Red Affinity'),
    ('green_affinity', 'Green Affinity'),
    ('blue_puzzle', 'Blue Puzzle Affinity'),
    ('red_puzzle', 'Red Puzzle Affinity'),
    ('green_puzzle', 'Green Puzzle Affinity'),
    ('ai_card', 'AI Card'),
    ('monster_level', 'Monster Level'),
    ('pumpkin', 'Pumpkin');

-- Seed data: known KDM versions
INSERT OR IGNORE INTO versions (name, description) VALUES
    ('1.0', 'Original 2015 Kickstarter release'),
    ('1.3', 'First major reprint / update'),
    ('1.5', '2017 revised edition'),
    ('1.6', 'Gamblers Chest era update');
