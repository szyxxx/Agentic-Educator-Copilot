import { NextRequest } from "next/server";
export const dynamic = "force-dynamic";
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path;
  if (path[0] !== "api" || path.some(p => !/^[a-zA-Z0-9_.-]+$/.test(p) || p === "..")) return Response.json({detail:"Jalur tidak valid."}, {status:400});
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(request.method);
  const expectedOrigin = process.env.APP_ORIGIN ?? request.nextUrl.origin;
  if (unsafe && request.headers.get("origin") !== expectedOrigin) return Response.json({detail:"Origin tidak diizinkan."}, {status:403});
  const headers = new Headers();
  for (const key of ["content-type", "accept"]) { const value = request.headers.get(key); if(value) headers.set(key,value); }
  const session = request.cookies.get("educopilot_session");
  if (session) headers.set("Cookie", `educopilot_session=${session.value}`);
  headers.set("Origin", process.env.APP_ORIGIN ?? "http://localhost:3000");
  try {
    const backend = new URL(process.env.API_BASE ?? "http://127.0.0.1:8000");
    let target = new URL(`/${path.join("/")}${request.nextUrl.search}`, backend);
    // Next's fetch wrapper may turn a forwarded body into a stream. Keep bytes
    // so FastAPI's slash redirect can be replayed without losing POST/form data.
    const bytes = unsafe ? new Uint8Array(await request.arrayBuffer()) : undefined;
    const send = (url: URL) => fetch(url, {
      method: request.method, headers, body: bytes,
      cache: "no-store", signal: request.signal, redirect: "manual",
    });
    let upstream = await send(target);
    for (let redirects = 0; [307, 308].includes(upstream.status) && redirects < 2; redirects++) {
      const location = upstream.headers.get("location");
      if (!location) break;
      const next = new URL(location, target);
      if (next.origin !== backend.origin || !next.pathname.startsWith("/api/")) {
        await upstream.body?.cancel();
        return Response.json({detail:"Redirect backend tidak diizinkan."}, {status:502});
      }
      await upstream.body?.cancel();
      target = next;
      upstream = await send(target);
    }
    if (upstream.status >= 300 && upstream.status < 400) {
      await upstream.body?.cancel();
      return Response.json({detail:"Redirect backend tidak dapat diselesaikan."}, {status:502});
    }
    const output = new Headers({"Cache-Control":"no-store"});
    for (const key of ["content-type", "content-disposition", "set-cookie"]) { const value=upstream.headers.get(key); if(value) output.set(key,value); }
    return new Response(upstream.body,{status:upstream.status,headers:output});
  } catch { return Response.json({detail:"Layanan backend tidak dapat dihubungi."},{status:503}); }
}
export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as HEAD };
