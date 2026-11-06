// Centralized API helpers so we don't sprinkle `http://127.0.0.1:8000` everywhere.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export function apiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function apiFetch<T = any>(
  path: string,
  init?: RequestInit & { json?: unknown }
): Promise<T> {
  const headers = new Headers(init?.headers);
  let body = init?.body;
  if (init?.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.json);
  }
  let res: Response;
  try {
    res = await fetch(apiUrl(path), {
    cache: "no-store",
    ...init,
    headers,
    body,
    });
  } catch {
    throw new Error("Layanan backend tidak dapat dihubungi. Coba lagi setelah beberapa saat.");
  }
  if (!res.ok) {
    const payload = await res.json().catch(() => null);
    const detail = typeof payload?.detail === "string" ? payload.detail : payload?.message;
    throw new Error(detail || `Layanan gagal memproses permintaan (HTTP ${res.status}). Silakan coba lagi.`);
  }
  // Tolerate empty 204 responses
  const text = await res.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}
