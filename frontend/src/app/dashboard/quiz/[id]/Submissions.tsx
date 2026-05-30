"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch, apiUrl } from "@/lib/api";

type Submission = {
  id: string;
  nim: string;
  name: string;
  answered_count: number;
  answers: Record<string, string>;
  status: "submitted" | "graded" | "unmatched";
  score: number | null;
  feedback: string | null;
};

type UploadReport = {
  added: number;
  matched: number;
  unmatched: { row: number; nim: string }[];
  skipped: { row: number; reason: string }[];
  missing_questions: string[];
  total_submissions: number;
};

type Props = {
  quizId: string;
  /** Refresh the parent quiz card after counts change. */
  onChange?: () => void;
};

export default function Submissions({ quizId, onChange }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [list, setList] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [report, setReport] = useState<UploadReport | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Submission[]>(
        `/api/quiz/${quizId}/submissions`
      );
      setList(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizId]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setReport(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(
        apiUrl(`/api/quiz/${quizId}/submissions/upload-csv`),
        { method: "POST", body: fd }
      );
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data: UploadReport = await res.json();
      setReport(data);
      await load();
      onChange?.();
    } catch (e: any) {
      alert(`Gagal upload CSV: ${e.message}`);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const handleDelete = async (id: string, nim: string) => {
    if (!confirm(`Hapus submission untuk NIM ${nim}?`)) return;
    await apiFetch(`/api/quiz/${quizId}/submissions/${id}`, {
      method: "DELETE",
    });
    await load();
    onChange?.();
  };

  const handleClearAll = async () => {
    if (!confirm("Hapus SEMUA submission untuk kuis ini?")) return;
    await apiFetch(`/api/quiz/${quizId}/submissions`, { method: "DELETE" });
    setReport(null);
    await load();
    onChange?.();
  };

  const counts = {
    matched: list.filter((s) => s.status !== "unmatched").length,
    unmatched: list.filter((s) => s.status === "unmatched").length,
  };

  const handleDownloadTemplate = () => {
    window.location.href = apiUrl(`/api/quiz/${quizId}/template.csv`);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Submission Mahasiswa</CardTitle>
            <CardDescription>
              Upload satu file CSV berisi jawaban kelas. Header wajib punya kolom{" "}
              <code className="text-[11px]">NIM Mahasiswa</code>, lalu kolom jawaban{" "}
              <code className="text-[11px]">PG-1, PG-2, ...</code> untuk pilihan ganda dan{" "}
              <code className="text-[11px]">ESSAY-1, ESSAY-2, ...</code> untuk esai.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
              }}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadTemplate}
              title="Unduh template CSV kosong sebagai panduan format"
            >
              ⬇ Template CSV
            </Button>
            <Button
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
            >
              {uploading ? "Memproses CSV..." : "📄 Upload CSV"}
            </Button>
            {list.length > 0 && (
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
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <Stat label="Total Submission" value={list.length} />
          <Stat label="Tercocokkan" value={counts.matched} accent="emerald" />
          <Stat label="Belum Cocok" value={counts.unmatched} accent="amber" />
        </div>

        {report && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm space-y-2">
            <p>
              <span className="font-semibold text-emerald-700">
                {report.added}
              </span>{" "}
              baris berhasil diproses
              {report.matched > 0 ? `, ${report.matched} tercocokkan ke roster` : ""}.
            </p>
            {report.missing_questions.length > 0 && (
              <p className="text-amber-700 text-xs">
                ⚠ Kolom CSV belum lengkap untuk soal:{" "}
                <code>{report.missing_questions.join(", ")}</code>. Soal-soal itu akan dianggap kosong.
              </p>
            )}
            {report.unmatched.length > 0 && (
              <details>
                <summary className="cursor-pointer text-amber-700">
                  ⚠️ {report.unmatched.length} baris dengan NIM tidak ada di roster
                </summary>
                <ul className="mt-2 space-y-0.5 text-xs text-slate-600">
                  {report.unmatched.slice(0, 50).map((u, i) => (
                    <li key={i}>
                      Baris {u.row} — NIM <strong>{u.nim}</strong>
                    </li>
                  ))}
                </ul>
              </details>
            )}
            {report.skipped.length > 0 && (
              <details>
                <summary className="cursor-pointer text-slate-600">
                  {report.skipped.length} baris dilewati
                </summary>
                <ul className="mt-2 space-y-0.5 text-xs text-slate-600">
                  {report.skipped.slice(0, 50).map((s, i) => (
                    <li key={i}>
                      Baris {s.row} — {s.reason}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-slate-500">Memuat...</p>
        ) : list.length === 0 ? (
          <p className="text-sm text-slate-500">
            Belum ada submission. Upload CSV jawaban mahasiswa.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 text-xs uppercase tracking-wide">
                  <th className="pb-2 pr-3">NIM</th>
                  <th className="pb-2 pr-3">Nama</th>
                  <th className="pb-2 pr-3">Terjawab</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">Skor</th>
                  <th className="pb-2 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {list.map((s) => (
                  <tr key={s.id}>
                    <td className="py-2 pr-3 font-mono text-slate-700">
                      {s.nim}
                    </td>
                    <td className="py-2 pr-3 text-slate-800">{s.name}</td>
                    <td className="py-2 pr-3 text-slate-500">
                      {s.answered_count} soal
                    </td>
                    <td className="py-2 pr-3">
                      {s.status === "graded" ? (
                        <Badge variant="success">Dinilai</Badge>
                      ) : s.status === "unmatched" ? (
                        <Badge variant="warning">Tidak Cocok</Badge>
                      ) : (
                        <Badge variant="outline">Submitted</Badge>
                      )}
                      {s.answered_count === 0 && (
                        <span
                          className="ml-2 text-[11px] text-slate-400"
                          title="Tidak ada jawaban yang terbaca dari CSV"
                        >
                          ⚠ kosong
                        </span>
                      )}
                    </td>
                    <td className="py-2 pr-3 text-slate-700">
                      {s.score == null ? "—" : s.score.toFixed(1)}
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
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: "emerald" | "amber";
}) {
  const accentClass =
    accent === "emerald"
      ? "text-emerald-600"
      : accent === "amber"
        ? "text-amber-600"
        : "text-slate-800";
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-xl font-semibold ${accentClass}`}>{value}</p>
    </div>
  );
}
