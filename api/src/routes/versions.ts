import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT v.name, COALESCE(v.description, '') as description,
              (SELECT COUNT(*) FROM gear g WHERE g.version = v.name) as count
       FROM versions v ORDER BY v.name`
    )
    .all() as { name: string; count: number; description: string }[];
  res.json(rows);
});

router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { name, description } = req.body;
  if (!name?.trim()) { res.status(400).json({ error: "Name is required" }); return; }
  const existing = db.prepare("SELECT name FROM versions WHERE name = ?").get(name.trim());
  if (existing) { res.status(409).json({ error: "Version already exists" }); return; }
  db.prepare("INSERT INTO versions (name, description) VALUES (?, ?)").run(name.trim(), description || "");
  res.status(201).json({ name: name.trim() });
});

router.get("/:name/items", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);
  const rows = db
    .prepare("SELECT g.id, g.name, g.type, g.expansion FROM gear g WHERE g.version = ? ORDER BY g.name")
    .all(name) as { id: number; name: string; type: string; expansion: string }[];
  res.json(rows);
});

router.put("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const oldName = decodeURIComponent(req.params.name);
  const { name: newName, description } = req.body;
  db.transaction(() => {
    if (newName?.trim() && newName.trim() !== oldName) {
      db.prepare("UPDATE gear SET version = ? WHERE version = ?").run(newName.trim(), oldName);
      db.prepare("DELETE FROM versions WHERE name = ?").run(oldName);
      db.prepare("INSERT OR REPLACE INTO versions (name, description) VALUES (?, ?)").run(newName.trim(), description ?? "");
    } else if (description !== undefined) {
      db.prepare("INSERT OR REPLACE INTO versions (name, description) VALUES (?, ?)").run(oldName, description);
    }
  })();
  res.json({ name: (newName?.trim() && newName.trim() !== oldName) ? newName.trim() : oldName });
});

router.delete("/:name", (req: Request, res: Response) => {
  const db = getDb();
  const name = decodeURIComponent(req.params.name);
  db.transaction(() => {
    db.prepare("UPDATE gear SET version = NULL WHERE version = ?").run(name);
    db.prepare("DELETE FROM versions WHERE name = ?").run(name);
  })();
  res.json({ deleted: name });
});

export default router;
