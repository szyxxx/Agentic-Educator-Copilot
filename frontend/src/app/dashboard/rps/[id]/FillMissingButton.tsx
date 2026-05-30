"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type Patch = { week: number; field: string; value: any };

export default function FillMissingButton({
  rpsId,
  status,
}: {
  rpsId: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  if (status === "validated") return null;

  const handle = async () => {
    if (!confirm(
      "Hanya field yang kosong yang akan diisi AI. Field yang sudah Anda tulis tidak diubah. Lanjutkan?"
    )) {
      return;
    }
    setBusy(true);
    try {
      const res = await apiFetch<{ patched: Patch[] }>(
        `/api/rps/${rpsId}/fill-missing`,
        { method: "POST" }
      );
      const count = res.patched?.length ?? 0;
      alert(
        count === 0
          ? "Tidak ada field kosong yang ditemukan."
          : `${count} field kosong sudah diisi AI. Periksa hasilnya di tabel pertemuan.`
      );
      router.refresh();
    } catch (e: any) {
      alert(`Gagal mengisi field kosong: ${e.message ?? e}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Button
      variant="outline"
      onClick={handle}
      disabled={busy}
      title="Isi otomatis hanya untuk field yang masih kosong; field yang sudah Anda tulis tidak akan diubah."
    >
      {busy ? "Mengisi…" : "🪄 Isi yang Kosong"}
    </Button>
  );
}
