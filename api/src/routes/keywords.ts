import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/keywords - list all keywords with counts and definitions
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT kd.keyword, COUNT(gk.id) as count, COALESCE(kd.definition, '') as definition
       FROM keyword_definitions kd
       LEFT JOIN gear_keywords gk ON kd.keyword = gk.keyword
       GROUP BY kd.keyword
       ORDER BY kd.keyword`
    )
    .all() as { keyword: string; count: number; definition: string }[];
  res.json(rows);
});

// POST /api/keywords - create a new keyword
router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { keyword, definition } = req.body;

  if (!keyword || !keyword.trim()) {
    res.status(400).json({ error: "Keyword name is required" });
    return;
  }

  const existing = db.prepare("SELECT keyword FROM keyword_definitions WHERE keyword = ?").get(keyword.trim());
  if (existing) {
    res.status(409).json({ error: "Keyword already exists" });
    return;
  }

  db.prepare("INSERT INTO keyword_definitions (keyword, definition) VALUES (?, ?)")
    .run(keyword.trim(), definition || "");

  res.status(201).json({ keyword: keyword.trim() });
});

// GET /api/keywords/:keyword/items - list gear items with this keyword
router.get("/:keyword/items", (req: Request, res: Response) => {
  const db = getDb();
  const keyword = decodeURIComponent(req.params.keyword);
  const rows = db
    .prepare(
      `SELECT g.id, g.name, g.type, g.expansion
       FROM gear g
       JOIN gear_keywords gk ON g.id = gk.gear_id
       WHERE gk.keyword = ?
       ORDER BY g.name`
    )
    .all(keyword) as { id: number; name: string; type: string; expansion: string }[];
  res.json(rows);
});

// PUT /api/keywords/:keyword - update keyword name and/or definition
router.put("/:keyword", (req: Request, res: Response) => {
  const db = getDb();
  const oldKeyword = decodeURIComponent(req.params.keyword);
  const { keyword: newKeyword, definition } = req.body;

  const transaction = db.transaction(() => {
    // Rename if new name provided and different
    if (newKeyword && newKeyword.trim() && newKeyword.trim() !== oldKeyword) {
      db.prepare("UPDATE gear_keywords SET keyword = ? WHERE keyword = ?")
        .run(newKeyword.trim(), oldKeyword);
      db.prepare("DELETE FROM keyword_definitions WHERE keyword = ?")
        .run(oldKeyword);
      db.prepare("INSERT OR REPLACE INTO keyword_definitions (keyword, definition) VALUES (?, ?)")
        .run(newKeyword.trim(), definition ?? "");
    } else if (definition !== undefined) {
      // Just update definition
      db.prepare("INSERT OR REPLACE INTO keyword_definitions (keyword, definition) VALUES (?, ?)")
        .run(oldKeyword, definition);
    }
  });

  transaction();
  const effectiveKeyword = (newKeyword && newKeyword.trim() !== oldKeyword) ? newKeyword.trim() : oldKeyword;
  res.json({ keyword: effectiveKeyword });
});

// DELETE /api/keywords/:keyword - remove a keyword from all items and its definition
router.delete("/:keyword", (req: Request, res: Response) => {
  const db = getDb();
  const keyword = decodeURIComponent(req.params.keyword);

  db.transaction(() => {
    db.prepare("DELETE FROM gear_keywords WHERE keyword = ?").run(keyword);
    db.prepare("DELETE FROM keyword_definitions WHERE keyword = ?").run(keyword);
  })();

  res.json({ deleted: keyword });
});

export default router;
