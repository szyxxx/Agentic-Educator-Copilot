import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { readResponse } from "./api-common";
export const API_BASE = process.env.API_BASE ?? "http://127.0.0.1:8000";
export function apiUrl(path: string): string { return `/api/backend${path}`; }
export async function apiFetch<T = any>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  if (!path.startsWith("/api/")) throw new Error("Jalur API tidak valid.");
  const cookie = (await cookies()).get("educopilot_session");
  const headers = new Headers(init?.headers);
  if (cookie) headers.set("Cookie", `educopilot_session=${cookie.value}`);
  headers.set("Origin", process.env.APP_ORIGIN ?? "http://localhost:3000");
  let body = init?.body;
  if (init?.json !== undefined) { headers.set("Content-Type", "application/json"); body = JSON.stringify(init.json); }
  let res: Response;
  try { res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init, headers, body }); }
  catch { throw new Error("Layanan backend tidak dapat dihubungi."); }
  if (res.status === 401) redirect("/login");
  return readResponse<T>(res);
}
