import { Router, Request, Response } from "express";
import { getDb, GearRow, KeywordRow, CraftingCostRow, SpecialRuleRow } from "../db.js";

const router = Router();

interface GearWithRelations extends GearRow {
  keywords: string[];
  special_rules: string[];
  crafting_costs: { resource: string; quantity: number }[];
}

function enrichGear(gear: GearRow): GearWithRelations {
  const db = getDb();
  const keywords = db
    .prepare("SELECT keyword FROM gear_keywords WHERE gear_id = ?")
    .all(gear.id) as KeywordRow[];
  const rules = db
    .prepare("SELECT rule FROM gear_special_rules WHERE gear_id = ?")
    .all(gear.id) as SpecialRuleRow[];
  const costs = db
    .prepare("SELECT resource, quantity FROM crafting_costs WHERE gear_id = ?")
    .all(gear.id) as CraftingCostRow[];

  return {
    ...gear,
    special_rules_names: gear.special_rules_names
      ? JSON.parse(gear.special_rules_names)
      : [],
    keywords: keywords.map((k) => k.keyword),
    special_rules: rules.map((r) => r.rule),
    crafting_costs: costs.map((c) => ({ resource: c.resource, quantity: c.quantity })),
  };
}

// GET /api/gear - list all gear with optional filters
router.get("/", (req: Request, res: Response) => {
  const db = getDb();
  const conditions: string[] = [];
  const params: unknown[] = [];

  if (req.query.type) {
    conditions.push("g.type = ?");
    params.push(req.query.type);
  }
  if (req.query.expansion) {
    conditions.push("g.expansion = ?");
    params.push(req.query.expansion);
  }
  if (req.query.search) {
    conditions.push("g.name LIKE ?");
    params.push(`%${req.query.search}%`);
  }
  if (req.query.keyword) {
    const keywords = String(req.query.keyword).split(",");
    const placeholders = keywords.map(() => "?").join(",");
    conditions.push(
      `g.id IN (SELECT gear_id FROM gear_keywords WHERE keyword IN (${placeholders}) GROUP BY gear_id HAVING COUNT(DISTINCT keyword) = ${keywords.length})`
    );
    params.push(...keywords);
  }
  if (req.query.rule) {
    const rules = String(req.query.rule).split(",");
    const placeholders = rules.map(() => "?").join(",");
    conditions.push(
      `g.id IN (SELECT gear_id FROM gear_special_rules WHERE rule IN (${placeholders}) GROUP BY gear_id HAVING COUNT(DISTINCT rule) = ${rules.length})`
    );
    params.push(...rules);
  }
  if (req.query.issues === "true") {
    conditions.push(
      `(g.type = 'other' OR g.image_path IS NULL OR g.affinity_top IS NULL)`
    );
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
  const rows = db
    .prepare(
      `SELECT g.id, g.name, g.type, g.expansion, g.category, g.version, g.image_path,
              g.speed, g.accuracy, g.strength, g.hit_location, g.armor_rating
       FROM gear g ${where}
       ORDER BY g.name`
    )
    .all(...params) as GearRow[];

  res.json(rows);
});

// GET /api/gear/:id - get a single gear item with all relations
router.get("/:id", (req: Request, res: Response) => {
  const db = getDb();
  const gear = db
    .prepare("SELECT * FROM gear WHERE id = ?")
    .get(req.params.id) as GearRow | undefined;

  if (!gear) {
    res.status(404).json({ error: "Gear not found" });
    return;
  }

  res.json(enrichGear(gear));
});

// PUT /api/gear/:id - update a gear item
router.put("/:id", (req: Request, res: Response) => {
  const db = getDb();
  const id = req.params.id;

  const existing = db.prepare("SELECT id FROM gear WHERE id = ?").get(id) as
    | { id: number }
    | undefined;
  if (!existing) {
    res.status(404).json({ error: "Gear not found" });
    return;
  }

  const {
    name, type, expansion, category, speed, accuracy, strength,
    hit_location, armor_rating, gained_by, card_text, crafting_location,
    special_rules_names, version, image_url, image_path,
    affinity_top, affinity_bottom, affinity_left, affinity_right,
    keywords, special_rules, crafting_costs,
  } = req.body;

  const updateGear = db.prepare(`
    UPDATE gear SET
      name = ?, type = ?, expansion = ?, category = ?,
      speed = ?, accuracy = ?, strength = ?,
      hit_location = ?, armor_rating = ?,
      gained_by = ?, card_text = ?, crafting_location = ?,
      special_rules_names = ?, version = ?,
      image_url = ?, image_path = ?,
      affinity_top = ?, affinity_bottom = ?, affinity_left = ?, affinity_right = ?
    WHERE id = ?
  `);

  const transaction = db.transaction(() => {
    updateGear.run(
      name, type, expansion, category,
      speed, accuracy, strength,
      hit_location, armor_rating,
      gained_by, card_text, crafting_location,
      JSON.stringify(special_rules_names || []), version,
      image_url, image_path,
      affinity_top, affinity_bottom, affinity_left, affinity_right,
      id
    );

    // Update keywords
    if (keywords !== undefined) {
      db.prepare("DELETE FROM gear_keywords WHERE gear_id = ?").run(id);
      const insertKw = db.prepare(
        "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)"
      );
      for (const kw of keywords) {
        insertKw.run(id, kw);
      }
    }

    // Update special rules
    if (special_rules !== undefined) {
      db.prepare("DELETE FROM gear_special_rules WHERE gear_id = ?").run(id);
      const insertRule = db.prepare(
        "INSERT INTO gear_special_rules (gear_id, rule) VALUES (?, ?)"
      );
      for (const rule of special_rules) {
        insertRule.run(id, rule);
      }
    }

    // Update crafting costs
    if (crafting_costs !== undefined) {
      db.prepare("DELETE FROM crafting_costs WHERE gear_id = ?").run(id);
      const insertCost = db.prepare(
        "INSERT INTO crafting_costs (gear_id, resource, quantity) VALUES (?, ?, ?)"
      );
      for (const cost of crafting_costs) {
        insertCost.run(id, cost.resource, cost.quantity);
      }
    }
  });

  transaction();

  const updated = db.prepare("SELECT * FROM gear WHERE id = ?").get(id) as GearRow;
  res.json(enrichGear(updated));
});

// POST /api/gear - create a new gear item
router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const {
    name, type, expansion, category, speed, accuracy, strength,
    hit_location, armor_rating, gained_by, card_text, crafting_location,
    special_rules_names, version, image_url, image_path,
    affinity_top, affinity_bottom, affinity_left, affinity_right,
    keywords, special_rules, crafting_costs,
  } = req.body;

  if (!name) {
    res.status(400).json({ error: "Name is required" });
    return;
  }

  const transaction = db.transaction(() => {
    const result = db
      .prepare(
        `INSERT INTO gear
         (name, type, expansion, category, speed, accuracy, strength,
          hit_location, armor_rating, gained_by, card_text, crafting_location,
          special_rules_names, version, image_url, image_path,
          affinity_top, affinity_bottom, affinity_left, affinity_right)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .run(
        name, type, expansion, category, speed, accuracy, strength,
        hit_location, armor_rating, gained_by, card_text, crafting_location,
        JSON.stringify(special_rules_names || []), version || "1.5",
        image_url, image_path,
        affinity_top, affinity_bottom, affinity_left, affinity_right
      );

    const gearId = result.lastInsertRowid;

    if (keywords) {
      const insertKw = db.prepare(
        "INSERT INTO gear_keywords (gear_id, keyword) VALUES (?, ?)"
      );
      for (const kw of keywords) {
        insertKw.run(gearId, kw);
      }
    }

    if (special_rules) {
      const insertRule = db.prepare(
        "INSERT INTO gear_special_rules (gear_id, rule) VALUES (?, ?)"
      );
      for (const rule of special_rules) {
        insertRule.run(gearId, rule);
      }
    }

    if (crafting_costs) {
      const insertCost = db.prepare(
        "INSERT INTO crafting_costs (gear_id, resource, quantity) VALUES (?, ?, ?)"
      );
      for (const cost of crafting_costs) {
        insertCost.run(gearId, cost.resource, cost.quantity);
      }
    }

    return gearId;
  });

  const gearId = transaction();
  const gear = db.prepare("SELECT * FROM gear WHERE id = ?").get(gearId) as GearRow;
  res.status(201).json(enrichGear(gear));
});

// DELETE /api/gear/:id
router.delete("/:id", (req: Request, res: Response) => {
  const db = getDb();
  const id = req.params.id;

  const existing = db.prepare("SELECT id FROM gear WHERE id = ?").get(id);
  if (!existing) {
    res.status(404).json({ error: "Gear not found" });
    return;
  }

  db.transaction(() => {
    db.prepare("DELETE FROM gear_keywords WHERE gear_id = ?").run(id);
    db.prepare("DELETE FROM gear_special_rules WHERE gear_id = ?").run(id);
    db.prepare("DELETE FROM crafting_costs WHERE gear_id = ?").run(id);
    db.prepare("DELETE FROM gear WHERE id = ?").run(id);
  })();

  res.status(204).send();
});

export default router;
