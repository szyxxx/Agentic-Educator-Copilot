"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch, apiUrl } from "@/lib/api";

type Student = {
  id: string;
  nim: string;
  name: string;
  email: string | null;
};

type Course = {
  id: string;
  name: string;
  code: string;
  sks: number;
  semester: number;
  program_study: string;
};

type Props = {
  courseId: string;
  course: Course | undefined;
};

const SAMPLE_CSV = `nim,nama,email
13520001,Andi Pratama,andi@kampus.ac.id
13520002,Budi Santoso,budi@kampus.ac.id
13520003,Citra Dewi,
`;

export default function StudentsView({ courseId, course }: Props) {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [draft, setDraft] = useState({ nim: "", name: "", email: "" });
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    added: number;
    skipped: { row: number; reason: string }[];
  } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Student[]>(
        `/api/students/?course_id=${courseId}`
      );
      setStudents(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  const handleAdd = async () => {
    if (!draft.nim.trim() || !draft.name.trim()) {
      alert("NIM dan Nama wajib diisi.");
      return;
    }
    setSaving(true);
    try {
      await apiFetch("/api/students/", {
        method: "POST",
        json: {
          course_id: courseId,
          nim: draft.nim.trim(),
          name: draft.name.trim(),
          email: draft.email.trim() || null,
        },
      });
      setDraft({ nim: "", name: "", email: "" });
      await load();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, nim: string) => {
    if (!confirm(`Hapus mahasiswa NIM ${nim}?`)) return;
    await apiFetch(`/api/students/${id}`, { method: "DELETE" });
    await load();
  };

  const handleClearAll = async () => {
    if (
      !confirm(
        `Hapus SEMUA ${students.length} mahasiswa dari mata kuliah ini? Aksi ini tidak bisa dibatalkan.`
      )
    )
      return;
    await apiFetch(`/api/students/?course_id=${courseId}`, {
      method: "DELETE",
    });
    await load();
  };

  const handleImport = async (file: File) => {
    setImporting(true);
    setImportResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(
        apiUrl(`/api/students/import?course_id=${courseId}`),
        { method: "POST", body: fd }
      );
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const data = await res.json();
      setImportResult(data);
      await load();
    } catch (e: any) {
      alert(`Gagal impor: ${e.message}`);
    } finally {
      setImporting(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const downloadTemplate = () => {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "template_mahasiswa.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const filtered = students.filter((s) => {
    if (!filter.trim()) return true;
    const q = filter.toLowerCase();
    return (
      s.nim.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q) ||
      (s.email || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
            Daftar Mahasiswa
          </p>
          <h1 className="text-3xl font-semibold">
            {course ? course.name : "Mata Kuliah"}
          </h1>
          {course && (
            <p className="mt-1 text-sm text-slate-500">
              {course.code} • {course.sks} SKS • Smt {course.semester}
              {course.program_study ? ` • ${course.program_study}` : ""}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/courses">
            <Button variant="outline">Kembali</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Mahasiswa</CardDescription>
            <CardTitle className="text-3xl">{students.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-slate-500">
              Terhitung dari yang terdaftar di sistem
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Dengan Email</CardDescription>
            <CardTitle className="text-3xl">
              {students.filter((s) => s.email).length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-slate-500">
              Bisa dikirim notifikasi langsung
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Tanpa Email</CardDescription>
            <CardTitle className="text-3xl">
              {students.filter((s) => !s.email).length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-slate-500">Lengkapi jika perlu</span>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Tambah Manual</CardTitle>
            <CardDescription>
              Isi NIM, Nama, dan Email (opsional) lalu Tambah.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1 block">
                  NIM
                </label>
                <input
                  type="text"
                  value={draft.nim}
                  onChange={(e) => setDraft({ ...draft, nim: e.target.value })}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  placeholder="13520001"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1 block">
                  Nama
                </label>
                <input
                  type="text"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  placeholder="Nama lengkap"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">
                Email (opsional)
              </label>
              <input
                type="email"
                value={draft.email}
                onChange={(e) => setDraft({ ...draft, email: e.target.value })}
                className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                placeholder="mahasiswa@kampus.ac.id"
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleAdd} disabled={saving}>
                {saving ? "Menyimpan..." : "+ Tambah"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Impor dari CSV</CardTitle>
            <CardDescription>
              Kolom yang dikenali: <code>nim</code>, <code>nama</code>/<code>name</code>, <code>email</code>. Pemisah koma atau titik koma.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleImport(f);
              }}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => fileInput.current?.click()}
                disabled={importing}
              >
                {importing ? "Mengimpor..." : "📥 Pilih File CSV"}
              </Button>
              <Button variant="outline" onClick={downloadTemplate}>
                Unduh Template
              </Button>
            </div>
            {importResult && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm space-y-2">
                <p>
                  <span className="font-semibold text-emerald-700">
                    {importResult.added}
                  </span>{" "}
                  mahasiswa berhasil ditambahkan.
                </p>
                {importResult.skipped.length > 0 && (
                  <details>
                    <summary className="cursor-pointer text-slate-600">
                      {importResult.skipped.length} baris dilewati
                    </summary>
                    <ul className="mt-2 space-y-0.5 text-xs text-slate-600">
                      {importResult.skipped.slice(0, 50).map((s, i) => (
                        <li key={i}>
                          baris {s.row}: {s.reason}
                        </li>
                      ))}
                      {importResult.skipped.length > 50 && (
                        <li>… dan {importResult.skipped.length - 50} lainnya</li>
                      )}
                    </ul>
                  </details>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Daftar Mahasiswa</CardTitle>
              <CardDescription>
                Klik tombol ✕ untuk menghapus seorang mahasiswa.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Cari NIM/nama/email..."
                className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm md:w-64"
              />
              {students.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-rose-600"
                  onClick={handleClearAll}
                >
                  Hapus Semua
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-slate-500">Memuat...</p>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-slate-500">
              {students.length === 0
                ? "Belum ada mahasiswa terdaftar. Tambah secara manual atau impor dari CSV."
                : "Tidak ada hasil untuk filter ini."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 text-xs uppercase tracking-wide">
                    <th className="pb-2 pr-3">NIM</th>
                    <th className="pb-2 pr-3">Nama</th>
                    <th className="pb-2 pr-3">Email</th>
                    <th className="pb-2 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((s) => (
                    <tr key={s.id}>
                      <td className="py-2 pr-3 font-mono text-slate-700">
                        {s.nim}
                      </td>
                      <td className="py-2 pr-3 text-slate-800">{s.name}</td>
                      <td className="py-2 pr-3 text-slate-500">
                        {s.email || "—"}
                      </td>
                      <td className="py-2 text-right">
                        <button
                          onClick={() => handleDelete(s.id, s.nim)}
                          className="text-rose-500 hover:underline text-xs"
                        >
                          Hapus
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
