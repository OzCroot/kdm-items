import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/locations - list all settlement locations with counts and definitions
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT sl.name, COALESCE(sl.definition, '') as definition,
              (SELECT COUNT(*) FROM gear g WHERE g.crafting_location = sl.name) as count
       FROM settlement_locations sl
       ORDER BY sl.name`
    )
    .all() as { name: string; count: number; definition: string }[];
  res.json(rows);
});

// POST /api/locations - create a new settlement location
router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { name, definition } = req.body;

  if (!name || !name.trim()) {
    res.status(400).json({ error: "Location name is required" });
    return;
  }

  const existing = db.prepare("SELECT name FROM settlement_locations WHERE name = ?").get(name.trim());
  if (existing) {
    res.status(409).json({ error: "Location already exists" });
    return;
  }

  db.prepare("INSERT INTO settlement_locations (name, definition) VALUES (?, ?)")
    .run(name.trim(), definition || "");

  res.status(201).json({ name: name.trim() });
});

// GET /api/locations/:name/items - list gear items at this location
router.get("/:name/items", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);
  const rows = db
    .prepare(
      `SELECT g.id, g.name, g.type, g.expansion
       FROM gear g
       WHERE g.crafting_location = ?
       ORDER BY g.name`
    )
    .all(name) as { id: number; name: string; type: string; expansion: string }[];
  res.json(rows);
});

// PUT /api/locations/:name - update name and/or definition
router.put("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const oldName = decodeURIComponent(req.params.name);
  const { name: newName, definition } = req.body;

  const transaction = db.transaction(() => {
    if (newName && newName.trim() && newName.trim() !== oldName) {
      // Rename in gear table too
      db.prepare("UPDATE gear SET crafting_location = ? WHERE crafting_location = ?")
        .run(newName.trim(), oldName);
      db.prepare("DELETE FROM settlement_locations WHERE name = ?")
        .run(oldName);
      db.prepare("INSERT OR REPLACE INTO settlement_locations (name, definition) VALUES (?, ?)")
        .run(newName.trim(), definition ?? "");
    } else if (definition !== undefined) {
      db.prepare("INSERT OR REPLACE INTO settlement_locations (name, definition) VALUES (?, ?)")
        .run(oldName, definition);
    }
  });

  transaction();
  const effectiveName = (newName && newName.trim() !== oldName) ? newName.trim() : oldName;
  res.json({ name: effectiveName });
});

// DELETE /api/locations/:name - remove a location (nulls crafting_location on gear)
router.delete("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);

  db.transaction(() => {
    db.prepare("UPDATE gear SET crafting_location = NULL WHERE crafting_location = ?").run(name);
    db.prepare("DELETE FROM settlement_locations WHERE name = ?").run(name);
  })();

  res.json({ deleted: name });
});

export default router;
