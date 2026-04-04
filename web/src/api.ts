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

export interface GearRef {
  id: number;
  name: string;
  type: string;
  expansion: string;
}

export function createKeyword(keyword: string, definition?: string) {
  return fetchJson("/api/keywords", {
    method: "POST",
    body: JSON.stringify({ keyword, definition: definition || "" }),
  });
}

export function listKeywordItems(keyword: string): Promise<GearRef[]> {
  return fetchJson(`/api/keywords/${encodeURIComponent(keyword)}/items`);
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

export function createSpecialRule(rule: string, definition?: string) {
  return fetchJson("/api/special-rules", {
    method: "POST",
    body: JSON.stringify({ rule, definition: definition || "" }),
  });
}

export function listSpecialRuleItems(rule: string): Promise<GearRef[]> {
  return fetchJson(`/api/special-rules/${encodeURIComponent(rule)}/items`);
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

// Settlement Locations
export interface LocationEntry {
  name: string;
  count: number;
  definition: string;
}

export function listLocationsWithCounts(): Promise<LocationEntry[]> {
  return fetchJson("/api/locations");
}

export async function listLocations(): Promise<string[]> {
  const rows = await listLocationsWithCounts();
  return rows.map((r) => r.name);
}

export function createLocation(name: string, definition?: string) {
  return fetchJson("/api/locations", {
    method: "POST",
    body: JSON.stringify({ name, definition: definition || "" }),
  });
}

export function listLocationItems(name: string): Promise<GearRef[]> {
  return fetchJson(`/api/locations/${encodeURIComponent(name)}/items`);
}

export function updateLocation(oldName: string, data: { name?: string; definition?: string }) {
  return fetchJson(`/api/locations/${encodeURIComponent(oldName)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteLocation(name: string) {
  return fetchJson(`/api/locations/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

// Versions
export interface VersionEntry {
  name: string;
  count: number;
  description: string;
}

export function listVersionsWithCounts(): Promise<VersionEntry[]> {
  return fetchJson("/api/versions");
}

export async function listVersions(): Promise<string[]> {
  const rows = await listVersionsWithCounts();
  return rows.map((r) => r.name);
}

export function createVersion(name: string, description?: string) {
  return fetchJson("/api/versions", { method: "POST", body: JSON.stringify({ name, description: description || "" }) });
}

export function listVersionItems(name: string): Promise<GearRef[]> {
  return fetchJson(`/api/versions/${encodeURIComponent(name)}/items`);
}

export function updateVersion(oldName: string, data: { name?: string; description?: string }) {
  return fetchJson(`/api/versions/${encodeURIComponent(oldName)}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteVersion(name: string) {
  return fetchJson(`/api/versions/${encodeURIComponent(name)}`, { method: "DELETE" });
}

// Expansions
export interface ExpansionEntry {
  name: string;
  count: number;
  description: string;
}

export function listExpansionsWithCounts(): Promise<ExpansionEntry[]> {
  return fetchJson("/api/expansions");
}

export async function listExpansions(): Promise<string[]> {
  const rows = await listExpansionsWithCounts();
  return rows.map((r) => r.name);
}

export function createExpansion(name: string, description?: string) {
  return fetchJson("/api/expansions", { method: "POST", body: JSON.stringify({ name, description: description || "" }) });
}

export function listExpansionItems(name: string): Promise<GearRef[]> {
  return fetchJson(`/api/expansions/${encodeURIComponent(name)}/items`);
}

export function updateExpansion(oldName: string, data: { name?: string; description?: string }) {
  return fetchJson(`/api/expansions/${encodeURIComponent(oldName)}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteExpansion(name: string) {
  return fetchJson(`/api/expansions/${encodeURIComponent(name)}`, { method: "DELETE" });
}

// Card Text Icons
export interface IconEntry {
  tag: string;
  display_name: string;
  icon_url: string;
  description: string;
}

export function listIcons(): Promise<IconEntry[]> {
  return fetchJson("/api/icons");
}

export function createIcon(tag: string, display_name: string, icon_url?: string, description?: string) {
  return fetchJson("/api/icons", { method: "POST", body: JSON.stringify({ tag, display_name, icon_url: icon_url || "", description: description || "" }) });
}

export function updateIcon(oldTag: string, data: { tag?: string; display_name?: string; icon_url?: string; description?: string }) {
  return fetchJson(`/api/icons/${encodeURIComponent(oldTag)}`, { method: "PUT", body: JSON.stringify(data) });
}

export function deleteIcon(tag: string) {
  return fetchJson(`/api/icons/${encodeURIComponent(tag)}`, { method: "DELETE" });
}

// Images
export function imageUrl(imagePath: string): string {
  return `${API_BASE}/api/images/${imagePath}`;
}
