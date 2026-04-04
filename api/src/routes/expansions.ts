import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT e.name, COALESCE(e.description, '') as description,
              (SELECT COUNT(*) FROM gear g WHERE g.expansion = e.name) as count
       FROM expansions e ORDER BY e.name`
    )
    .all() as { name: string; count: number; description: string }[];
  res.json(rows);
});

router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { name, description } = req.body;
  if (!name?.trim()) { res.status(400).json({ error: "Name is required" }); return; }
  const existing = db.prepare("SELECT name FROM expansions WHERE name = ?").get(name.trim());
  if (existing) { res.status(409).json({ error: "Expansion already exists" }); return; }
  db.prepare("INSERT INTO expansions (name, description) VALUES (?, ?)").run(name.trim(), description || "");
  res.status(201).json({ name: name.trim() });
});

router.get("/:name/items", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);
  const rows = db
    .prepare("SELECT g.id, g.name, g.type, g.expansion FROM gear g WHERE g.expansion = ? ORDER BY g.name")
    .all(name) as { id: number; name: string; type: string; expansion: string }[];
  res.json(rows);
});

router.put("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const oldName = decodeURIComponent(req.params.name);
  const { name: newName, description } = req.body;
  db.transaction(() => {
    if (newName?.trim() && newName.trim() !== oldName) {
      db.prepare("UPDATE gear SET expansion = ? WHERE expansion = ?").run(newName.trim(), oldName);
      db.prepare("DELETE FROM expansions WHERE name = ?").run(oldName);
      db.prepare("INSERT OR REPLACE INTO expansions (name, description) VALUES (?, ?)").run(newName.trim(), description ?? "");
    } else if (description !== undefined) {
      db.prepare("INSERT OR REPLACE INTO expansions (name, description) VALUES (?, ?)").run(oldName, description);
    }
  })();
  res.json({ name: (newName?.trim() && newName.trim() !== oldName) ? newName.trim() : oldName });
});

router.delete("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);
  db.transaction(() => {
    db.prepare("UPDATE gear SET expansion = NULL WHERE expansion = ?").run(name);
    db.prepare("DELETE FROM expansions WHERE name = ?").run(name);
  })();
  res.json({ deleted: name });
});

export default router;
