"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Material = {
  id: string;
  title: string;
  topic: string;
  type: string;
  url: string | null;
  week: number;
  cpmk: string;
  status: string;
  status_text: string;
  updated_at: string;
  size: string;
};

type MaterialContent = {
  id: string;
  title: string;
  type: string;
  content_text: string;
  url: string | null;
  course_id: string;
  rps_id: string;
};

type Course = { id: string; name: string; code: string };

type Props = {
  data: {
    summary: { label: string; value: string; note: string }[];
    materials: Material[];
  };
  courses: Course[];
};

export function KnowledgeView({ data, courses }: Props) {
  const router = useRouter();
  const [showAdd, setShowAdd] = useState(false);
  const [saving, setSaving] = useState(false);
  const [viewContent, setViewContent] = useState<MaterialContent | null>(null);
  const [viewLoading, setViewLoading] = useState(false);
  const [draft, setDraft] = useState({
    course_id: courses[0]?.id ?? "",
    title: "",
    topic: "",
    material_type: "URL",
    week: 1,
    cpmk: "",
    size: "-",
  });

  const handleAdd = async () => {
    if (!draft.course_id || !draft.title.trim()) {
      alert("Mata kuliah dan judul wajib diisi.");
      return;
    }
    setSaving(true);
    try {
      await apiFetch("/api/materials/", { method: "POST", json: draft });
      setShowAdd(false);
      setDraft({ ...draft, title: "", topic: "", cpmk: "" });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menambah materi: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Hapus materi "${title}"?`)) return;
    try {
      await apiFetch(`/api/materials/${id}`, { method: "DELETE" });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menghapus: ${e.message}`);
    }
  };

  const handleView = async (material: Material) => {
    // For URL-only materials without extracted content, just open the URL
    if (material.type === "URL" && material.url) {
      window.open(material.url, "_blank");
      return;
    }
    setViewLoading(true);
    try {
      const content = await apiFetch<MaterialContent>(
        `/api/materials/${material.id}/content`
      );
      setViewContent(content);
    } catch (e: any) {
      alert(`Gagal memuat konten: ${e.message}`);
    } finally {
      setViewLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <p className="text-sm text-slate-500">
          Silabus, jurnal, dan tautan yang dipakai AI sebagai konteks saat membuat RPS atau kuis. Materi dengan ekstraksi teks akan otomatis terindeks ke RAG.
        </p>
        <Button onClick={() => setShowAdd(true)}>+ Tambah Materi</Button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {data.summary.map((item) => (
          <Card key={item.label}>
            <CardHeader className="pb-2">
              <CardDescription>{item.label}</CardDescription>
              <CardTitle className="text-3xl">{item.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-xs text-slate-500">{item.note}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {data.materials.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              Belum ada materi terdaftar.
            </CardContent>
          </Card>
        )}
        {data.materials.map((material) => (
          <Card key={material.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{material.title}</CardTitle>
                  <CardDescription>{material.topic}</CardDescription>
                </div>
                <Badge
                  variant={material.status === "ready" ? "success" : "warning"}
                >
                  {material.status_text}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-xs text-slate-500">
                {material.type} • Minggu {material.week}{" "}
                {material.cpmk ? `• ${material.cpmk}` : ""}
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span>Terakhir diupdate: {material.updated_at}</span>
                <span className="h-1 w-1 rounded-full bg-slate-300" />
                <span>Ukuran: {material.size}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleView(material)}
                  disabled={viewLoading}
                >
                  {viewLoading ? "Memuat..." : "👁 Lihat"}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-rose-600"
                  onClick={() => handleDelete(material.id, material.title)}
                >
                  Hapus
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4">
            <h2 className="text-xl font-semibold">Tambah Materi</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1 block">
                  Mata Kuliah
                </label>
                <select
                  value={draft.course_id}
                  onChange={(e) =>
                    setDraft({ ...draft, course_id: e.target.value })
                  }
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                >
                  <option value="">Pilih mata kuliah...</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} — {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <Field
                label="Judul"
                value={draft.title}
                onChange={(v) => setDraft({ ...draft, title: v })}
              />
              <Field
                label="Topik"
                value={draft.topic}
                onChange={(v) => setDraft({ ...draft, topic: v })}
              />
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">
                    Tipe
                  </label>
                  <select
                    value={draft.material_type}
                    onChange={(e) =>
                      setDraft({ ...draft, material_type: e.target.value })
                    }
                    className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  >
                    <option value="URL">URL</option>
                    <option value="PDF">PDF</option>
                    <option value="DOCX">DOCX</option>
                    <option value="PPT">PPT</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 mb-1 block">
                    Minggu
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={16}
                    value={draft.week}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        week: parseInt(e.target.value) || 1,
                      })
                    }
                    className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  />
                </div>
                <Field
                  label="CPMK"
                  value={draft.cpmk}
                  onChange={(v) => setDraft({ ...draft, cpmk: v })}
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setShowAdd(false)}>
                Batal
              </Button>
              <Button onClick={handleAdd} disabled={saving}>
                {saving ? "Menyimpan..." : "Simpan"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* View Content Modal */}
      {viewContent && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4"
          onClick={() => setViewContent(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl flex flex-col"
            style={{ maxHeight: "85vh" }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between px-6 pt-5 pb-4 border-b border-slate-100">
              <div className="min-w-0 pr-4">
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">
                  {viewContent.type}
                </p>
                <h2 className="text-xl font-semibold text-slate-900 leading-snug">
                  {viewContent.title}
                </h2>
              </div>
              <button
                onClick={() => setViewContent(null)}
                className="shrink-0 text-slate-400 hover:text-slate-700 text-2xl leading-none mt-0.5"
                aria-label="Tutup"
              >
                ×
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {viewContent.content_text ? (
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-700">
                  {viewContent.content_text}
                </pre>
              ) : viewContent.url ? (
                <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
                  <p className="text-slate-500 text-sm">
                    Konten teks tidak tersedia. Buka tautan asli untuk membaca materi ini.
                  </p>
                  <a
                    href={viewContent.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 transition-colors"
                  >
                    🔗 Buka Tautan
                  </a>
                </div>
              ) : (
                <p className="text-slate-400 text-sm italic text-center py-12">
                  Konten belum tersedia untuk materi ini.
                </p>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                {viewContent.content_text
                  ? `${viewContent.content_text.length.toLocaleString()} karakter diekstrak`
                  : "Tidak ada teks terekstrak"}
              </span>
              <Button variant="outline" size="sm" onClick={() => setViewContent(null)}>
                Tutup
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-500 mb-1 block">
        {label}
      </label>
      <input
        type="text"
        className="w-full p-2 border rounded-lg text-sm bg-slate-50"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
