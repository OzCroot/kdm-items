import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare("SELECT tag, display_name, icon_url, description FROM card_text_icons ORDER BY tag")
    .all() as { tag: string; display_name: string; icon_url: string; description: string }[];
  res.json(rows);
});

router.post("/", (req: Request, res: Response) => {
  const db = getDb();
  const { tag, display_name, icon_url, description } = req.body;
  if (!tag?.trim()) { res.status(400).json({ error: "Tag is required" }); return; }
  const existing = db.prepare("SELECT tag FROM card_text_icons WHERE tag = ?").get(tag.trim());
  if (existing) { res.status(409).json({ error: "Icon tag already exists" }); return; }
  db.prepare("INSERT INTO card_text_icons (tag, display_name, icon_url, description) VALUES (?, ?, ?, ?)")
    .run(tag.trim(), display_name || tag.trim(), icon_url || "", description || "");
  res.status(201).json({ tag: tag.trim() });
});

router.put("/:tag", (req: Request, res: Response) => {
  const db = getDb();
  const oldTag = decodeURIComponent(req.params.tag);
  const { tag: newTag, display_name, icon_url, description } = req.body;
  db.transaction(() => {
    if (newTag?.trim() && newTag.trim() !== oldTag) {
      // Update references in card_text
      const items = db.prepare("SELECT id, card_text FROM gear WHERE card_text LIKE ?").all(`%[${oldTag}]%`) as { id: number; card_text: string }[];
      for (const item of items) {
        const updated = item.card_text.replaceAll(`[${oldTag}]`, `[${newTag.trim()}]`);
        db.prepare("UPDATE gear SET card_text = ? WHERE id = ?").run(updated, item.id);
      }
      db.prepare("DELETE FROM card_text_icons WHERE tag = ?").run(oldTag);
      db.prepare("INSERT INTO card_text_icons (tag, display_name, icon_url, description) VALUES (?, ?, ?, ?)")
        .run(newTag.trim(), display_name ?? "", icon_url ?? "", description ?? "");
    } else {
      if (display_name !== undefined) db.prepare("UPDATE card_text_icons SET display_name = ? WHERE tag = ?").run(display_name, oldTag);
      if (icon_url !== undefined) db.prepare("UPDATE card_text_icons SET icon_url = ? WHERE tag = ?").run(icon_url, oldTag);
      if (description !== undefined) db.prepare("UPDATE card_text_icons SET description = ? WHERE tag = ?").run(description, oldTag);
    }
  })();
  res.json({ tag: (newTag?.trim() && newTag.trim() !== oldTag) ? newTag.trim() : oldTag });
});

router.delete("/:tag", (req: Request, res: Response) => {
  const db = getDb();
  const tag = decodeURIComponent(req.params.tag);
  db.prepare("DELETE FROM card_text_icons WHERE tag = ?").run(tag);
  res.json({ deleted: tag });
});

export default router;
