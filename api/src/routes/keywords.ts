import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/keywords - list all keywords with counts and definitions
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT gk.keyword, COUNT(*) as count, COALESCE(kd.definition, '') as definition
       FROM gear_keywords gk
       LEFT JOIN keyword_definitions kd ON gk.keyword = kd.keyword
       GROUP BY gk.keyword
       ORDER BY gk.keyword`
    )
    .all() as { keyword: string; count: number; definition: string }[];
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
