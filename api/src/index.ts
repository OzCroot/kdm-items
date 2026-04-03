import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import gearRouter from "./routes/gear.js";
import keywordsRouter from "./routes/keywords.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = parseInt(process.env.PORT || "3000", 10);
const IMAGES_PATH = process.env.IMAGES_PATH || path.resolve(__dirname, "../../data/images");

app.use(cors());
app.use(express.json());

// API routes
app.use("/api/gear", gearRouter);
app.use("/api/keywords", keywordsRouter);

// Serve card images
app.use("/api/images", express.static(IMAGES_PATH));

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`KDM Items API listening on port ${PORT}`);
  console.log(`Images served from: ${IMAGES_PATH}`);
});
