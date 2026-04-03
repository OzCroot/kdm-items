export interface GearListItem {
  id: number;
  name: string;
  type: string | null;
  expansion: string | null;
  category: string | null;
  version: string | null;
  image_path: string | null;
  speed: string | null;
  accuracy: string | null;
  strength: string | null;
  hit_location: string | null;
  armor_rating: string | null;
}

export interface CraftingCost {
  resource: string;
  quantity: number;
}

export interface GearDetail extends GearListItem {
  url: string | null;
  gained_by: string | null;
  card_text: string | null;
  crafting_location: string | null;
  special_rules_names: string[];
  image_url: string | null;
  affinity_top: string | null;
  affinity_bottom: string | null;
  affinity_left: string | null;
  affinity_right: string | null;
  keywords: string[];
  special_rules: string[];
  crafting_costs: CraftingCost[];
}
