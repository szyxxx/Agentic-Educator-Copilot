"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch, apiUrl } from "@/lib/api";

type Material = {
  id: string;
  title: string;
  type: string;
  week: number;
  course_id: string;
  has_content: boolean;
};

type Props = {
  /** When set, only materials for this course are shown. */
  courseId: string;
  /** Called whenever the picker decides to update the textarea content. */
  onUseMaterial: (text: string) => void;
};

/**
 * Pulls existing Knowledge Hub materials and lets the user use them as
 * AI quiz reference, plus a quick upload button that round-trips through
 * the same Knowledge Hub.
 */
export function KnowledgeMaterialPicker({ courseId, onUseMaterial }: Props) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const qs = courseId ? `?course_id=${courseId}` : "";
      const data = await apiFetch<Material[]>(`/api/materials/${qs}`);
      setMaterials(data);
      // Drop previously picked items that no longer match the course
      setPicked((prev) => {
        const valid = new Set(data.map((m) => m.id));
        const next = new Set<string>();
        prev.forEach((id) => valid.has(id) && next.add(id));
        return next;
      });
    } catch (e) {
      console.error("Failed to load materials", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  const toggle = (id: string) => {
    setPicked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleUseSelected = async () => {
    if (picked.size === 0) {
      alert("Pilih minimal satu materi terlebih dahulu.");
      return;
    }
    setBusy(true);
    try {
      const ids = Array.from(picked);
      const fetched = await Promise.all(
        ids.map((id) =>
          apiFetch<{ title: string; content_text: string }>(
            `/api/materials/${id}/content`
          )
        )
      );
      const blocks = fetched
        .filter((f) => f.content_text && f.content_text.trim().length > 0)
        .map((f) => `--- ${f.title} ---\n${f.content_text}`);
      if (blocks.length === 0) {
        alert(
          "Materi yang dipilih belum punya teks terindeks. Upload ulang sebagai PDF/TXT."
        );
        return;
      }
      onUseMaterial(blocks.join("\n\n"));
    } catch (e: any) {
      alert(`Gagal mengambil konten: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (file: File) => {
    if (!courseId) {
      alert("Pilih mata kuliah terlebih dahulu sebelum mengunggah.");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("course_id", courseId);
      fd.append("title", file.name);
      fd.append("week", "1");
      fd.append("file", file);
      const res = await fetch(apiUrl("/api/materials/upload"), {
        method: "POST",
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      // Mark the new material as picked, then refresh and immediately load its
      // content into the textarea so the user can review it.
      await load();
      setPicked((prev) => new Set(prev).add(data.id));
      const c = await apiFetch<{ title: string; content_text: string }>(
        `/api/materials/${data.id}/content`
      );
      if (c.content_text) {
        onUseMaterial(`--- ${c.title} ---\n${c.content_text}`);
      }
    } catch (e: any) {
      alert(`Gagal upload: ${e.message || e}`);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-800">
            Pilih dari Knowledge Hub
          </p>
          <p className="text-xs text-slate-500">
            Materi yang sudah Anda unggah dapat dipakai langsung sebagai acuan AI.
          </p>
        </div>
        <div className="flex items-center gap-2">
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
            onClick={() => fileInput.current?.click()}
            disabled={uploading || !courseId}
            title={!courseId ? "Pilih mata kuliah dulu" : "Upload PDF baru"}
          >
            {uploading ? "Mengunggah…" : "+ Upload Baru"}
          </Button>
          <Button
            size="sm"
            onClick={handleUseSelected}
            disabled={busy || picked.size === 0}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            {busy ? "Memuat…" : `Gunakan ${picked.size || ""}`.trim()}
          </Button>
        </div>
      </div>

      {loading ? (
        <p className="text-xs text-slate-500">Memuat materi…</p>
      ) : materials.length === 0 ? (
        <p className="text-xs text-slate-500">
          {courseId
            ? "Belum ada materi untuk mata kuliah ini. Upload PDF baru di atas atau buka Knowledge Hub."
            : "Pilih mata kuliah terlebih dahulu untuk melihat materinya."}
        </p>
      ) : (
        <ul className="max-h-48 overflow-y-auto divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {materials.map((m) => (
            <li
              key={m.id}
              className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50"
            >
              <input
                type="checkbox"
                checked={picked.has(m.id)}
                onChange={() => toggle(m.id)}
                className="rounded text-teal-600"
              />
              <Badge
                variant={m.has_content ? "success" : "outline"}
                className="text-[10px] px-1.5 py-0"
              >
                {m.type}
              </Badge>
              <span
                className="truncate max-w-[260px] text-slate-700"
                title={m.title}
              >
                {m.title}
              </span>
              <span className="ml-auto text-[11px] text-slate-400">
                Minggu {m.week}
                {!m.has_content && " • belum terindeks"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
