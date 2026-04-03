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

export function listKeywords(): Promise<string[]> {
  return fetchJson("/api/keywords");
}

export function imageUrl(imagePath: string): string {
  return `${API_BASE}/api/images/${imagePath}`;
}
