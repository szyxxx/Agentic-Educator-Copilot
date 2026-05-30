"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type Props = {
  rpsId: string;
  weekNumber: number;
  initialFeedback: string;
  status: string;
};

/** Inline feedback button + modal for a single meeting row. */
export default function WeekFeedback({
  rpsId,
  weekNumber,
  initialFeedback,
  status,
}: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [feedback, setFeedback] = useState(initialFeedback);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  if (status === "validated" || status === "compliant") return null;

  const hasFeedback = (initialFeedback || "").trim().length > 0;

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiFetch(
        `/api/rps/${rpsId}/meetings/${weekNumber}/feedback`,
        { method: "POST", json: { feedback } }
      );
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await apiFetch(
        `/api/rps/${rpsId}/meetings/${weekNumber}/regenerate`,
        { method: "POST", json: { feedback } }
      );
      setOpen(false);
      router.refresh();
    } catch (e: any) {
      alert(`Gagal regenerasi: ${e.message}`);
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={`text-[11px] inline-flex items-center gap-1 px-2 py-1 rounded-full border transition ${
          hasFeedback
            ? "border-amber-300 bg-amber-50 text-amber-700"
            : "border-slate-200 text-slate-500 hover:border-slate-300"
        }`}
        title={hasFeedback ? "Ada feedback tersimpan" : "Beri feedback / regenerasi"}
      >
        {hasFeedback ? "💬 Feedback" : "+ Feedback"}
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4">
            <div>
              <h2 className="text-lg font-semibold">
                Feedback Minggu {weekNumber}
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Tuliskan apa yang ingin diperbaiki di pertemuan ini. AI akan menyusun ulang topik, metode, evaluasi, dan referensi sesuai catatan ini.
              </p>
            </div>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Contoh: Topik terlalu teoretis, ganti dengan studi kasus implementasi industri."
              className="w-full min-h-[120px] p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/40"
            />
            <div className="flex justify-between items-center">
              <Button
                variant="ghost"
                onClick={() => setOpen(false)}
                disabled={saving || regenerating}
              >
                Tutup
              </Button>
              <div className="flex gap-2">
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
                  {regenerating ? "Memproses…" : "✨ Regenerate"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
