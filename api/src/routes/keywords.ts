import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/keywords - list all distinct keywords
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare("SELECT DISTINCT keyword FROM gear_keywords ORDER BY keyword")
    .all() as { keyword: string }[];
  res.json(rows.map((r) => r.keyword));
});

export default router;
