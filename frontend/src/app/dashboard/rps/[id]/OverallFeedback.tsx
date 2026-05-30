"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Props = {
  rpsId: string;
  initialFeedback: string;
  status: string;
};

/** Overall feedback + full-RPS regenerate. Hidden when RPS is approved. */
export default function OverallFeedback({
  rpsId,
  initialFeedback,
  status,
}: Props) {
  const router = useRouter();
  const [feedback, setFeedback] = useState(initialFeedback);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  if (status === "validated" || status === "compliant") return null;

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiFetch(`/api/rps/${rpsId}/feedback`, {
        method: "POST",
        json: { feedback },
      });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan feedback: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    if (
      !confirm(
        "Regenerasi seluruh RPS dengan AI? Konten saat ini akan ditimpa (referensi tetap dipertahankan)."
      )
    ) {
      return;
    }
    setRegenerating(true);
    try {
      await apiFetch(`/api/rps/${rpsId}/regenerate`, {
        method: "POST",
        json: { feedback },
      });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal regenerasi: ${e.message}`);
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <Card className="border-amber-200/80 bg-amber-50/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          ✍️ Catatan Dosen
        </CardTitle>
        <CardDescription>
          Catatan bebas untuk diri sendiri atau untuk dipertimbangkan AI saat regenerasi RPS berikutnya.
          Untuk umpan balik per pertemuan, gunakan kolom internal di setiap baris tabel pertemuan.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Contoh: Tambahkan studi kasus industri pada minggu 3-5, perkuat evaluasi praktikum di paruh kedua semester."
          className="w-full min-h-[100px] p-3 border border-amber-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400/40"
        />
        <div className="flex flex-wrap gap-2 justify-end">
          <Button
            variant="outline"
            onClick={handleSave}
            disabled={saving || regenerating}
          >
            {saving ? "Menyimpan…" : "Simpan Feedback"}
          </Button>
          <Button
            onClick={handleRegenerate}
            disabled={regenerating || saving}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {regenerating ? "AI sedang regenerasi (1–2 menit)…" : "✨ Regenerate Seluruh RPS"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
