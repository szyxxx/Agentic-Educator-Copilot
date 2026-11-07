import { navigateToFreshSession } from "@/lib/session-navigation";
import { readResponse } from "./api-common";
// Same-origin BFF keeps HttpOnly sessions available to uploads and downloads.
export const API_BASE = "/api/backend";
export function apiUrl(path: string): string {
  if (!path.startsWith("/api/")) throw new Error("Jalur API tidak valid.");
  return `${API_BASE}${path}`;
}
export async function apiFetch<T = any>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const headers = new Headers(init?.headers);
  let body = init?.body;
  if (init?.json !== undefined) { headers.set("Content-Type", "application/json"); body = JSON.stringify(init.json); }
  let res: Response;
  try { res = await fetch(apiUrl(path), { cache: "no-store", ...init, headers, body, credentials: "same-origin" }); }
  catch { throw new Error("Layanan backend tidak dapat dihubungi. Coba lagi setelah beberapa saat."); }
  if (res.status === 401 && typeof window !== "undefined" && !path.endsWith("/login")) navigateToFreshSession("/login");
  return readResponse<T>(res);
}
