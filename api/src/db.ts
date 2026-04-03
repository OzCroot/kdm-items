import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = process.env.DB_PATH || path.resolve(__dirname, "../../data/kdm_gear.db");

let db: Database.Database;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.pragma("foreign_keys = ON");
  }
  return db;
}

export interface GearRow {
  id: number;
  name: string;
  type: string | null;
  expansion: string | null;
  category: string | null;
  url: string | null;
  speed: string | null;
  accuracy: string | null;
  strength: string | null;
  hit_location: string | null;
  armor_rating: string | null;
  gained_by: string | null;
  card_text: string | null;
  crafting_location: string | null;
  special_rules_names: string | null;
  version: string | null;
  image_url: string | null;
  image_path: string | null;
  affinity_top: string | null;
  affinity_bottom: string | null;
  affinity_left: string | null;
  affinity_right: string | null;
}

export interface KeywordRow {
  id: number;
  gear_id: number;
  keyword: string;
}

export interface CraftingCostRow {
  id: number;
  gear_id: number;
  resource: string;
  quantity: number;
}
