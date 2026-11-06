"use client";

import { Button } from "@/components/ui/button";

export default function DashboardError() {
  return (
    <section role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-slate-900">
      <h1 className="text-xl font-semibold">Data belum dapat dimuat</h1>
      <p className="mt-2 max-w-prose text-sm">
        Layanan mungkin sedang mengalami gangguan. Coba lagi setelah beberapa saat.
        Data yang belum dimuat tidak ditampilkan sebagai data kosong.
      </p>
      <Button className="mt-4" onClick={() => window.location.reload()}>Coba lagi</Button>
    </section>
  );
}
