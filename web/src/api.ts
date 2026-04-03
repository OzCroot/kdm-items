import type { GearListItem, GearDetail } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:3000";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Gear
export function listGear(params?: Record<string, string>): Promise<GearListItem[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchJson(`/api/gear${qs}`);
}

export function getGear(id: number): Promise<GearDetail> {
  return fetchJson(`/api/gear/${id}`);
}

export function updateGear(id: number, data: Partial<GearDetail>): Promise<GearDetail> {
  return fetchJson(`/api/gear/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function createGear(data: Partial<GearDetail>): Promise<GearDetail> {
  return fetchJson("/api/gear", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteGear(id: number): Promise<void> {
  return fetchJson(`/api/gear/${id}`, { method: "DELETE" });
}

// Keywords
export interface KeywordEntry {
  keyword: string;
  count: number;
  definition: string;
}

export function listKeywordsWithCounts(): Promise<KeywordEntry[]> {
  return fetchJson("/api/keywords");
}

export async function listKeywords(): Promise<string[]> {
  const rows = await listKeywordsWithCounts();
  return rows.map((r) => r.keyword);
}

export function updateKeyword(oldKeyword: string, data: { keyword?: string; definition?: string }) {
  return fetchJson(`/api/keywords/${encodeURIComponent(oldKeyword)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteKeyword(keyword: string) {
  return fetchJson(`/api/keywords/${encodeURIComponent(keyword)}`, {
    method: "DELETE",
  });
}

// Special Rules
export interface SpecialRuleEntry {
  rule: string;
  count: number;
  definition: string;
}

export function listSpecialRulesWithCounts(): Promise<SpecialRuleEntry[]> {
  return fetchJson("/api/special-rules");
}

export async function listSpecialRules(): Promise<string[]> {
  const rows = await listSpecialRulesWithCounts();
  return rows.map((r) => r.rule);
}

export function updateSpecialRule(oldRule: string, data: { rule?: string; definition?: string }) {
  return fetchJson(`/api/special-rules/${encodeURIComponent(oldRule)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteSpecialRule(rule: string) {
  return fetchJson(`/api/special-rules/${encodeURIComponent(rule)}`, {
    method: "DELETE",
  });
}

// Images
export function imageUrl(imagePath: string): string {
  return `${API_BASE}/api/images/${imagePath}`;
}
