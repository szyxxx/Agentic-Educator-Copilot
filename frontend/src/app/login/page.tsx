"use client";

import { navigateToFreshSession } from "@/lib/session-navigation";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
export default function Login() {
  const [username,setUsername]=useState("");const [password,setPassword]=useState("");const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  return <main className="mx-auto flex min-h-screen max-w-md items-center p-6"><form className="w-full space-y-5 rounded-3xl border bg-white p-8 shadow-sm" onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");try{await apiFetch("/api/auth/login",{method:"POST",json:{username,password}});navigateToFreshSession("/dashboard");}catch(e){setError((e as Error).message);setBusy(false);}}}>
    <p className="text-xs uppercase tracking-widest text-slate-500">EduCopilot</p><h1 className="text-3xl font-semibold">Masuk ke ruang kerja</h1><p className="text-sm text-slate-600">Gunakan akun yang dibuat admin layanan.</p>
    <label className="block text-sm">Nama akun<input name="username" autoComplete="username" required value={username} onChange={e=>setUsername(e.target.value)} className="mt-2 w-full rounded-xl border p-3"/></label>
    <label className="block text-sm">Password<input name="password" type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} className="mt-2 w-full rounded-xl border p-3"/></label>
    {error&&<p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<Button type="submit" disabled={busy} className="w-full">{busy?"Memeriksa…":"Masuk"}</Button>
  </form></main>;
}
