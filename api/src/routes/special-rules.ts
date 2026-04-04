import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/special-rules - list all rules with counts and definitions
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT srd.rule, COUNT(gsr.id) as count, COALESCE(srd.definition, '') as definition
       FROM special_rule_definitions srd
       LEFT JOIN gear_special_rules gsr ON srd.rule = gsr.rule
       GROUP BY srd.rule
       ORDER BY srd.rule`
    )
    .all() as { rule: string; count: number; definition: string }[];
  res.json(rows);
});

// POST /api/special-rules - create a new rule
router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { rule, definition } = req.body;

  if (!rule || !rule.trim()) {
    res.status(400).json({ error: "Rule name is required" });
    return;
  }

  const existing = db.prepare("SELECT rule FROM special_rule_definitions WHERE rule = ?").get(rule.trim());
  if (existing) {
    res.status(409).json({ error: "Rule already exists" });
    return;
  }

  db.prepare("INSERT INTO special_rule_definitions (rule, definition) VALUES (?, ?)")
    .run(rule.trim(), definition || "");

  res.status(201).json({ rule: rule.trim() });
});

// GET /api/special-rules/:rule/items - list gear items with this rule
router.get("/:rule/items", (req: Request, res: Response) => {
  const db = getDb();
  const rule = decodeURIComponent(req.params.rule);
  const rows = db
    .prepare(
      `SELECT g.id, g.name, g.type, g.expansion
       FROM gear g
       JOIN gear_special_rules gsr ON g.id = gsr.gear_id
       WHERE gsr.rule = ?
       ORDER BY g.name`
    )
    .all(rule) as { id: number; name: string; type: string; expansion: string }[];
  res.json(rows);
});

// PUT /api/special-rules/:rule - update rule name and/or definition
router.put("/:rule", (req: Request, res: Response) => {
  const db = getDb();
  const oldRule = decodeURIComponent(req.params.rule);
  const { rule: newRule, definition } = req.body;

  const transaction = db.transaction(() => {
    if (newRule && newRule.trim() && newRule.trim() !== oldRule) {
      db.prepare("UPDATE gear_special_rules SET rule = ? WHERE rule = ?")
        .run(newRule.trim(), oldRule);
      db.prepare("DELETE FROM special_rule_definitions WHERE rule = ?")
        .run(oldRule);
      db.prepare("INSERT OR REPLACE INTO special_rule_definitions (rule, definition) VALUES (?, ?)")
        .run(newRule.trim(), definition ?? "");
    } else if (definition !== undefined) {
      db.prepare("INSERT OR REPLACE INTO special_rule_definitions (rule, definition) VALUES (?, ?)")
        .run(oldRule, definition);
    }
  });

  transaction();
  const effectiveRule = (newRule && newRule.trim() !== oldRule) ? newRule.trim() : oldRule;
  res.json({ rule: effectiveRule });
});

// DELETE /api/special-rules/:rule - remove a rule from all items and its definition
router.delete("/:rule", (req: Request, res: Response) => {
  const db = getDb();
  const rule = decodeURIComponent(req.params.rule);

  db.transaction(() => {
    db.prepare("DELETE FROM gear_special_rules WHERE rule = ?").run(rule);
    db.prepare("DELETE FROM special_rule_definitions WHERE rule = ?").run(rule);
  })();

  res.json({ deleted: rule });
});

export default router;
