import { Router, Request, Response } from "express";
import { getDb } from "../db.js";

const router = Router();

// GET /api/special-rules - list all distinct special rules
router.get("/", (_req: Request, res: Response) => {
  const db = getDb();
  const rows = db
    .prepare("SELECT DISTINCT rule FROM gear_special_rules ORDER BY rule")
    .all() as { rule: string }[];
  res.json(rows.map((r) => r.rule));
});

export default router;
