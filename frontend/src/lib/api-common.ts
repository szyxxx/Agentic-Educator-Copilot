export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function readResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const payload = await res.json().catch(() => null);
    const detail = typeof payload?.detail === "string" ? payload.detail : payload?.message;
    throw new ApiError(detail || `Permintaan gagal (HTTP ${res.status}).`, res.status);
  }
  const text = await res.text();
  return text ? JSON.parse(text) as T : undefined as T;
}
