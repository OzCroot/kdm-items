export interface GearItem {
  id: number;
  name: string;
  type: string | null;
  expansion: string | null;
  speed: string | null;
  accuracy: string | null;
  strength: string | null;
  hit_location: string | null;
  armor_rating: string | null;
  card_text: string | null;
  image_path: string | null;
  affinity_top: string | null;
  affinity_bottom: string | null;
  affinity_left: string | null;
  affinity_right: string | null;
  keywords: string[];
  special_rules: string[];
}

export type AffinityColor = "red" | "green" | "blue";

export interface AffinityLink {
  from: [number, number]; // [row, col]
  to: [number, number];
  color: AffinityColor;
  direction: "horizontal" | "vertical";
}

export type GridCell = GearItem | null;
export type Grid = GridCell[][];

export interface SavedGrid {
  name: string;
  grid: (number | null)[][]; // stores gear IDs
  timestamp: number;
}
