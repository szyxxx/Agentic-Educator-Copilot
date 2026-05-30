"use client";

import { useState } from "react";
import Link from "next/link";
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

type Course = {
  id: string;
  name: string;
  code: string;
  sks: number;
  semester: number;
  program_study: string;
  students: number;
  avg_score: number;
  active_quizzes: number;
  status: string;
  status_text: string;
  updated_at: string;
};

type Props = {
  data: { summary: { label: string; value: string; note: string }[]; items: Course[] };
};

export function CoursesView({ data }: Props) {
  const router = useRouter();
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState({
    name: "",
    code: "",
    sks: 3,
    semester: 1,
    program_study: "",
  });

  const handleCreate = async () => {
    if (!draft.name.trim() || !draft.code.trim()) {
      alert("Nama dan kode mata kuliah wajib diisi.");
      return;
    }
    setSaving(true);
    try {
      await apiFetch("/api/courses/", { method: "POST", json: draft });
      setShowCreate(false);
      setDraft({ name: "", code: "", sks: 3, semester: 1, program_study: "" });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menambah mata kuliah: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Hapus mata kuliah "${name}"? RPS, kuis, dan materi terkait juga akan dihapus.`)) return;
    try {
      await apiFetch(`/api/courses/${id}`, { method: "DELETE" });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menghapus: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">📚 Mata Kuliah Saya</h1>
          <p className="mt-1 text-sm text-slate-500">
            Daftar mata kuliah yang Anda ampu. Akses analitik, kelola RPS, dan buat kuis langsung dari sini.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ Tambah Mata Kuliah</Button>
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
        {data.items.map((course) => (
          <Card key={course.id}>
            <CardHeader>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="text-xl">{course.name}</CardTitle>
                  <CardDescription>
                    {course.code} • {course.sks} SKS • Smt {course.semester}
                  </CardDescription>
                </div>
                <Badge variant={course.status === "ok" ? "success" : "warning"}>
                  {course.status_text}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <Stat label="Jumlah Mahasiswa" value={course.students} />
                <Stat label="Rata-rata Nilai" value={course.avg_score} />
                <Stat label="Kuis Aktif" value={course.active_quizzes} />
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Link href={`/dashboard/courses/${course.id}/students`}>
                  <Button size="sm" variant="default">
                    👥 Mahasiswa ({course.students})
                  </Button>
                </Link>
                <Link href={`/dashboard/analytics?course_id=${course.id}`}>
                  <Button size="sm" variant="secondary">
                    Lihat Analitik
                  </Button>
                </Link>
                <Link href={`/dashboard/rps/new?course_id=${course.id}`}>
                  <Button size="sm" variant="outline">
                    Buat / Kelola RPS
                  </Button>
                </Link>
                <Link href={`/dashboard/quiz/new?course_id=${course.id}`}>
                  <Button size="sm" variant="ghost">
                    + Buat Kuis
                  </Button>
                </Link>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-rose-600"
                  onClick={() => handleDelete(course.id, course.name)}
                >
                  Hapus
                </Button>
                <span className="ml-auto text-xs text-slate-500">
                  Update: {course.updated_at}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-xl font-semibold">Tambah Mata Kuliah</h2>
            <div className="space-y-3">
              <Field
                label="Nama Mata Kuliah"
                value={draft.name}
                onChange={(v) => setDraft({ ...draft, name: v })}
              />
              <Field
                label="Kode"
                value={draft.code}
                onChange={(v) => setDraft({ ...draft, code: v })}
              />
              <Field
                label="Program Studi"
                value={draft.program_study}
                onChange={(v) => setDraft({ ...draft, program_study: v })}
              />
              <div className="grid grid-cols-2 gap-3">
                <NumberField
                  label="SKS"
                  value={draft.sks}
                  onChange={(v) => setDraft({ ...draft, sks: v })}
                />
                <NumberField
                  label="Semester"
                  value={draft.semester}
                  onChange={(v) => setDraft({ ...draft, semester: v })}
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={() => setShowCreate(false)}>
                Batal
              </Button>
              <Button onClick={handleCreate} disabled={saving}>
                {saving ? "Menyimpan..." : "Simpan"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
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

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-500 mb-1 block">
        {label}
      </label>
      <input
        type="number"
        className="w-full p-2 border rounded-lg text-sm bg-slate-50"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value) || 0)}
      />
    </div>
  );
}
