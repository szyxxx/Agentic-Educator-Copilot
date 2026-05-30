"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch, apiUrl } from "@/lib/api";

type Material = {
  id: string;
  title: string;
  type: string;
  url: string | null;
  week: number;
  cpmk: string;
  course_id: string;
  rps_id: string | null;
  status_text: string;
  has_content: boolean;
};

type Props = {
  rpsId: string;
  courseId: string;
  weekNumber: number;
  cpmk: string;
};

/**
 * Compact uploader / picker shown next to each meeting row.
 *
 * Supports:
 *   1. Uploading a brand-new file (PDF/DOCX/TXT) — extracted + indexed + linked here.
 *   2. Picking an existing Knowledge Hub material for the same course and
 *      attaching it to this week.
 *   3. Detaching (delete = remove the material from this week, but it stays
 *      in the Knowledge Hub list when detached vs. fully deleted).
 */
export default function WeekMaterials({
  rpsId,
  courseId,
  weekNumber,
  cpmk,
}: Props) {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Material[]>([]);
  const [available, setAvailable] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [attached, courseWide] = await Promise.all([
        apiFetch<Material[]>(
          `/api/materials/?rps_id=${rpsId}&week=${weekNumber}`
        ),
        courseId
          ? apiFetch<Material[]>(`/api/materials/?course_id=${courseId}`)
          : Promise.resolve([] as Material[]),
      ]);
      setItems(attached);
      const attachedIds = new Set(attached.map((m) => m.id));
      // Anything in the same course that isn't already on this week is fair game
      setAvailable(courseWide.filter((m) => !attachedIds.has(m.id)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rpsId, weekNumber, courseId]);

  const handleUpload = async (file: File) => {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("rps_id", rpsId);
      fd.append("course_id", courseId || "");
      fd.append("title", file.name);
      fd.append("week", String(weekNumber));
      fd.append("cpmk", cpmk || "");
      fd.append("file", file);
      const res = await fetch(apiUrl("/api/materials/upload"), {
        method: "POST",
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      await load();
      router.refresh();
    } catch (e: any) {
      alert(`Gagal upload: ${e.message || e}`);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const handleAttach = async (materialId: string) => {
    setBusy(true);
    try {
      await apiFetch(`/api/materials/${materialId}`, {
        method: "PATCH",
        json: { rps_id: rpsId, week: weekNumber, cpmk: cpmk || "" },
      });
      setPickerOpen(false);
      await load();
      router.refresh();
    } catch (e: any) {
      alert(`Gagal melampirkan: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleDetach = async (materialId: string) => {
    if (!confirm("Lepas materi dari minggu ini? File tetap tersimpan di Knowledge Hub.")) return;
    try {
      await apiFetch(`/api/materials/${materialId}`, {
        method: "PATCH",
        json: { rps_id: "", week: 0 },
      });
      await load();
      router.refresh();
    } catch (e: any) {
      alert(`Gagal melepas: ${e.message}`);
    }
  };

  return (
    <div className="space-y-1.5">
      {loading ? (
        <span className="text-[11px] text-slate-400">memuat…</span>
      ) : items.length === 0 ? (
        <span className="text-[11px] text-slate-400 italic">
          belum ada materi
        </span>
      ) : (
        <ul className="space-y-1">
          {items.map((m) => (
            <li key={m.id} className="flex items-center gap-1.5">
              <Badge
                variant={m.has_content ? "success" : "outline"}
                className="text-[10px] px-1.5 py-0"
              >
                {m.type}
              </Badge>
              <span
                className="truncate max-w-[160px] text-[11px] text-slate-700"
                title={m.title}
              >
                {m.url ? (
                  <a
                    href={m.url}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:underline"
                  >
                    {m.title}
                  </a>
                ) : (
                  m.title
                )}
              </span>
              <button
                onClick={() => handleDetach(m.id)}
                className="text-rose-500 text-[11px] hover:underline ml-auto"
                aria-label="Lepas materi"
                title="Lepas dari minggu ini (tetap di Knowledge Hub)"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center gap-1 flex-wrap">
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleUpload(f);
          }}
        />
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-[11px] px-2"
          onClick={() => fileInput.current?.click()}
          disabled={busy}
        >
          {busy ? "…" : "+ Upload"}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-[11px] px-2"
          onClick={() => setPickerOpen(true)}
          disabled={busy || available.length === 0}
          title={
            available.length === 0
              ? "Belum ada materi lain untuk mata kuliah ini"
              : `Pilih dari ${available.length} materi yang sudah ada`
          }
        >
          📚 Pilih
        </Button>
      </div>

      {pickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-5 space-y-3">
            <div>
              <h3 className="text-base font-semibold text-slate-800">
                Lampirkan Materi ke Minggu {weekNumber}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Pilih dari materi mata kuliah ini yang sudah diunggah sebelumnya.
              </p>
            </div>

            {available.length === 0 ? (
              <p className="text-sm text-slate-500 italic">
                Belum ada materi lain untuk mata kuliah ini.
              </p>
            ) : (
              <ul className="max-h-72 overflow-y-auto divide-y divide-slate-200 rounded-lg border border-slate-200">
                {available.map((m) => (
                  <li
                    key={m.id}
                    className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50"
                  >
                    <Badge
                      variant={m.has_content ? "success" : "outline"}
                      className="text-[10px] px-1.5 py-0"
                    >
                      {m.type}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <p
                        className="truncate text-slate-700"
                        title={m.title}
                      >
                        {m.title}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        {m.rps_id ? `Sebelumnya minggu ${m.week}` : "Belum dilampirkan"}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-[11px] px-2"
                      onClick={() => handleAttach(m.id)}
                      disabled={busy}
                    >
                      Pilih
                    </Button>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex justify-end pt-1">
              <Button
                variant="ghost"
                onClick={() => setPickerOpen(false)}
                disabled={busy}
              >
                Tutup
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
