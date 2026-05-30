"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MultiSelect } from "@/components/ui/multi-select";
import { apiFetch, apiUrl } from "@/lib/api";

const metodeOptions = [
  "Ceramah",
  "Diskusi",
  "Problem-Based Learning",
  "Project-Based Learning",
  "Studi Kasus",
  "Praktikum",
  "Demo",
  "Self-Paced Learning",
  "Flipped Classroom",
  "Tanya Jawab",
];
const modalitasOptions = [
  "Tatap Muka",
  "Daring Sinkron",
  "Daring Asinkron",
  "Hybrid (Bauran)",
];
const evaluasiOptions = [
  "Kuis",
  "Tugas Individu",
  "Tugas Kelompok",
  "Presentasi",
  "Ujian Tulis",
  "Ujian Lisan",
  "Proyek Kelompok",
  "Laporan Akhir",
  "Tanya Jawab",
  "Review Jurnal",
];

export type RpsMeeting = {
  week: number;
  /** Higher-level subject area, must match an entry in the parent RPS's bahan_kajian. */
  bahan_kajian_topik: string;
  /** Bold weekly title in the institutional template. */
  sub_topic_title: string;
  /** Description that follows the title and colon. */
  sub_topic_description: string;
  /** 1-based integer index into the parent RPS's cpmk_list, or null. */
  cpmk_number: number | null;
  /** 1-based integer indices into the parent RPS's references_list. */
  reference_indices: number[];
  /** Internal pedagogy field — hidden behind Advanced disclosure. */
  method: string;
  /** Internal pedagogy field — hidden behind Advanced disclosure. */
  evaluation: string;
};

export type RpsFormData = {
  course_name: string;
  course_code: string;
  sks: number;
  semester: number;
  program_study: string;
  cpl_list: string[];
  cpmk_list: string[];
  references_list: string[];
  bahan_kajian: string[];
  learning_methods: string[];
  learning_modality: string;
  meetings: RpsMeeting[];
};

const UTS_MODULE = 8;
const UAS_MODULE = 16;
const UTS_TITLE = "Ujian Tengah Semester (UTS)";
const UAS_TITLE = "Ujian Akhir Semester (UAS)";

const isExamWeek = (week: number) =>
  week === UTS_MODULE || week === UAS_MODULE;

const examTitleFor = (week: number) =>
  week === UTS_MODULE ? UTS_TITLE : week === UAS_MODULE ? UAS_TITLE : "";

const blankMeetings = (): RpsMeeting[] =>
  Array.from({ length: 16 }, (_, i) => {
    const week = i + 1;
    return {
      week,
      bahan_kajian_topik: "",
      sub_topic_title: examTitleFor(week),
      sub_topic_description: "",
      cpmk_number: null,
      reference_indices: [],
      method: "",
      evaluation: "",
    };
  });

export const blankRps = (): RpsFormData => ({
  course_name: "",
  course_code: "",
  sks: 3,
  semester: 1,
  program_study: "",
  cpl_list: [""],
  cpmk_list: [""],
  references_list: [""],
  bahan_kajian: [""],
  learning_methods: [],
  learning_modality: "",
  meetings: blankMeetings(),
});

const loadingSteps = [
  { label: "Menganalisis mata kuliah & tren industri...", pct: 10 },
  { label: "Menyusun Capaian Pembelajaran (CPL & CPMK)...", pct: 25 },
  { label: "Mencari referensi jurnal & pustaka terkait...", pct: 45 },
  { label: "Merancang rencana 16 pertemuan...", pct: 65 },
  { label: "Menyelaraskan dengan standar SN-Dikti...", pct: 80 },
  { label: "Memvalidasi dokumen RPS akhir...", pct: 92 },
  { label: "Hampir selesai, menyimpan hasil...", pct: 98 },
];

type Props = {
  mode: "new" | "edit";
  rpsId?: string;
  initialData: RpsFormData;
  /** When in edit mode the course banner is shown instead of editable fields. */
  courseLabel?: string;
};

export default function RpsForm({ mode, rpsId, initialData, courseLabel }: Props) {
  const router = useRouter();
  const [data, setData] = useState<RpsFormData>(initialData);
  const [saving, setSaving] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiStep, setAiStep] = useState(0);
  const [aiExtras, setAiExtras] = useState({
    description: "",
    learning_method_preference: "hybrid",
  });
  const [aiLinks, setAiLinks] = useState<string[]>([""]);
  const [aiPdf, setAiPdf] = useState<File | null>(null);

  useEffect(() => {
    if (!aiBusy) return;
    setAiStep(0);
    const t = setInterval(() => {
      setAiStep((p) => Math.min(p + 1, loadingSteps.length - 1));
    }, 5000);
    return () => clearInterval(t);
  }, [aiBusy]);

  const handleSave = async () => {
    setSaving(true);
    try {
      if (mode === "edit" && rpsId) {
        await apiFetch(`/api/rps/${rpsId}`, { method: "PUT", json: data });
        router.push(`/dashboard/rps/${rpsId}`);
      } else {
        const res = await apiFetch<{ rps_id: string }>(`/api/rps/`, {
          method: "POST",
          json: data,
        });
        router.push(`/dashboard/rps/${res.rps_id}`);
      }
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan RPS: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleAiGenerate = async () => {
    setAiOpen(false);
    setAiBusy(true);
    try {
      const fd = new FormData();
      fd.append("course_name", data.course_name || "Mata Kuliah Baru");
      fd.append("course_code", data.course_code || "NEW");
      fd.append("sks", String(data.sks || 3));
      fd.append("semester", String(data.semester || 1));
      fd.append("program_study", data.program_study || "");
      fd.append("description", aiExtras.description);
      fd.append(
        "learning_method_preference",
        aiExtras.learning_method_preference
      );
      fd.append(
        "bahan_kajian",
        JSON.stringify(data.bahan_kajian.filter((b) => b.trim() !== ""))
      );
      fd.append(
        "learning_methods",
        JSON.stringify(data.learning_methods.filter((m) => m.trim() !== ""))
      );
      fd.append("learning_modality", data.learning_modality || "");
      // Send what the dosen already typed so the AI fills in the gaps
      // instead of overwriting the dosen's CPL/CPMK/References.
      fd.append(
        "cpl_list",
        JSON.stringify(data.cpl_list.filter((c) => c.trim() !== ""))
      );
      fd.append(
        "cpmk_list",
        JSON.stringify(data.cpmk_list.filter((c) => c.trim() !== ""))
      );
      fd.append(
        "references_list",
        JSON.stringify(data.references_list.filter((r) => r.trim() !== ""))
      );
      fd.append(
        "links",
        JSON.stringify(aiLinks.filter((l) => l.trim() !== ""))
      );
      if (aiPdf) fd.append("pdf_file", aiPdf);

      const res = await fetch(apiUrl("/api/rps/generate"), {
        method: "POST",
        body: fd,
      });
      const json = await res.json();
      if (!res.ok) {
        alert(`Gagal membuat RPS dengan AI: ${JSON.stringify(json)}`);
        setAiBusy(false);
        return;
      }
      const newId = json?.data?.rps_id;
      if (newId) {
        router.push(`/dashboard/rps/${newId}/edit`);
      } else {
        router.push("/dashboard/rps");
      }
    } catch (e: any) {
      alert(`Terjadi kesalahan jaringan: ${e.message}`);
      setAiBusy(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {aiBusy && <AiOverlay step={aiStep} />}
      {aiOpen && (
        <AiModal
          courseName={data.course_name}
          courseCode={data.course_code}
          description={aiExtras.description}
          links={aiLinks}
          onChangeCourseName={(v) => setData({ ...data, course_name: v })}
          onChangeCourseCode={(v) => setData({ ...data, course_code: v })}
          onChangeDescription={(v) =>
            setAiExtras({ ...aiExtras, description: v })
          }
          onChangeLinks={setAiLinks}
          onPickPdf={setAiPdf}
          onCancel={() => setAiOpen(false)}
          onSubmit={handleAiGenerate}
        />
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/60 shadow-sm">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-teal-600 font-semibold mb-1">
            {mode === "new" ? "Mode Pembuatan" : "Mode Edit"}
          </p>
          <h1 className="text-3xl font-semibold text-slate-800">
            {mode === "new" ? "Buat RPS Baru" : "Edit RPS"}
          </h1>
          {courseLabel && (
            <p className="mt-1 text-sm text-slate-500">{courseLabel}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={
              mode === "edit" && rpsId
                ? `/dashboard/rps/${rpsId}`
                : `/dashboard/rps`
            }
          >
            <Button variant="outline" className="border-slate-300">
              Batal
            </Button>
          </Link>
          {mode === "new" && (
            <Button
              onClick={() => setAiOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm shadow-indigo-600/20"
            >
              ✨ Auto-Generate AI
            </Button>
          )}
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-teal-600 hover:bg-teal-700 text-white shadow-sm shadow-teal-600/20"
          >
            {saving
              ? "Menyimpan..."
              : mode === "edit"
                ? "Simpan Perubahan"
                : "Simpan Manual"}
          </Button>
        </div>
      </div>

      {mode === "new" && (
        <Card>
          <CardHeader>
            <CardTitle>Informasi Mata Kuliah</CardTitle>
            <CardDescription>
              Detail dasar mata kuliah. Field ini sama untuk pembuatan manual maupun AI.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="col-span-2">
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Nama Mata Kuliah
                </label>
                <input
                  type="text"
                  className="w-full p-2.5 border rounded-lg text-sm font-semibold bg-slate-50"
                  value={data.course_name}
                  onChange={(e) =>
                    setData({ ...data, course_name: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Kode
                </label>
                <input
                  type="text"
                  className="w-full p-2.5 border rounded-lg text-sm bg-slate-50"
                  value={data.course_code}
                  onChange={(e) =>
                    setData({ ...data, course_code: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Program Studi
                </label>
                <input
                  type="text"
                  className="w-full p-2.5 border rounded-lg text-sm bg-slate-50"
                  value={data.program_study}
                  onChange={(e) =>
                    setData({ ...data, program_study: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  SKS
                </label>
                <input
                  type="number"
                  min={1}
                  max={6}
                  className="w-full p-2.5 border rounded-lg text-sm bg-slate-50"
                  value={data.sks}
                  onChange={(e) =>
                    setData({ ...data, sks: parseInt(e.target.value) || 0 })
                  }
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Semester
                </label>
                <input
                  type="number"
                  min={1}
                  max={8}
                  className="w-full p-2.5 border rounded-lg text-sm bg-slate-50"
                  value={data.semester}
                  onChange={(e) =>
                    setData({
                      ...data,
                      semester: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ListCard
            title="Capaian Pembelajaran Lulusan (CPL)"
            description="Kompetensi lulusan program studi"
            label="CPL"
            badgeClass="bg-teal-50 text-teal-700"
            items={data.cpl_list}
            onChange={(items) => setData({ ...data, cpl_list: items })}
          />
          <ListCard
            title="Capaian Pembelajaran Mata Kuliah (CPMK)"
            description="Target kompetensi mata kuliah. Setiap pertemuan akan dipetakan ke salah satu nomor CPMK di sini."
            label="CPMK"
            badgeClass="bg-indigo-50 text-indigo-700"
            items={data.cpmk_list}
            onChange={(items) => {
              // If a CPMK was removed, clear cpmk_number on affected meetings.
              const newLen = items.length;
              const meetings = data.meetings.map((m) =>
                m.cpmk_number !== null && m.cpmk_number > newLen
                  ? { ...m, cpmk_number: null }
                  : m
              );
              setData({ ...data, cpmk_list: items, meetings });
            }}
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Referensi & Pustaka</CardTitle>
            <CardDescription>
              Tambahkan buku, jurnal, dan tautan yang dipakai sebagai sumber utama.
              Penomoran 1, 2, 3, ... otomatis dipakai oleh kolom "No. Referensi" di setiap pertemuan.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <NumberedReferencesEditor
              items={data.references_list}
              onMutate={(next, indexRemap) => {
                const meetings = data.meetings.map((m) => ({
                  ...m,
                  reference_indices: (m.reference_indices || [])
                    .map((idx) => indexRemap[idx] ?? null)
                    .filter((v): v is number => typeof v === "number"),
                }));
                setData({ ...data, references_list: next, meetings });
              }}
            />
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Bahan Kajian</CardTitle>
              <CardDescription>
                Topik atau pokok bahasan yang akan dicakup mata kuliah.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PlainList
                items={data.bahan_kajian}
                placeholder="Contoh: Pencarian heuristik, jaringan saraf tiruan..."
                onChange={(items) => {
                  // If a Bahan Kajian was removed, clear bahan_kajian_topik
                  // on every meeting that referenced it.
                  const allowed = new Set(items.filter(Boolean));
                  const meetings = data.meetings.map((m) =>
                    m.bahan_kajian_topik && !allowed.has(m.bahan_kajian_topik)
                      ? { ...m, bahan_kajian_topik: "" }
                      : m
                  );
                  setData({ ...data, bahan_kajian: items, meetings });
                }}
                addLabel="+ Tambah Bahan Kajian"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Metode & Modalitas</CardTitle>
              <CardDescription>
                Strategi pembelajaran tingkat mata kuliah yang akan diturunkan ke setiap pertemuan.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Metode Pembelajaran
                </label>
                <MultiSelect
                  options={metodeOptions}
                  value={data.learning_methods.join(", ")}
                  placeholder="Pilih metode utama..."
                  onChange={(val) => {
                    const arr = val
                      .split(/[,&]+/)
                      .map((v) => v.trim())
                      .filter(Boolean);
                    setData({ ...data, learning_methods: arr });
                  }}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Modalitas Pembelajaran
                </label>
                <select
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                  value={data.learning_modality}
                  onChange={(e) =>
                    setData({ ...data, learning_modality: e.target.value })
                  }
                >
                  <option value="">Pilih modalitas...</option>
                  {modalitasOptions.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Rencana 16 Pertemuan</CardTitle>
          <CardDescription>
            Sesuai template institusi: Modul 1–16, dua kolom topik (Bahan Kajian/Topik + Sub-Topik), nomor CPMK, dan kutipan referensi.
            Modul 8 dan 16 terkunci untuk UTS/UAS.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.meetings.map((m, idx) => (
              <MeetingRow
                key={idx}
                meeting={m}
                bahanKajianOptions={data.bahan_kajian}
                cpmkList={data.cpmk_list}
                referencesList={data.references_list}
                metodeOptions={metodeOptions}
                evaluasiOptions={evaluasiOptions}
                onChange={(next) => {
                  const arr = [...data.meetings];
                  arr[idx] = next;
                  setData({ ...data, meetings: arr });
                }}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ListCard({
  title,
  description,
  label,
  badgeClass,
  items,
  onChange,
}: {
  title: string;
  description: string;
  label: string;
  badgeClass: string;
  items: string[];
  onChange: (items: string[]) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item, idx) => (
            <div key={idx} className="flex gap-3 items-start">
              <div className="flex-shrink-0 pt-3">
                <span
                  className={`inline-flex items-center justify-center px-2 py-1 text-xs font-semibold rounded-md ${badgeClass}`}
                >
                  {label}-{idx + 1}
                </span>
              </div>
              <textarea
                className="flex-1 min-h-[60px] p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                value={item}
                placeholder="Masukkan deskripsi..."
                onChange={(e) => {
                  const next = [...items];
                  next[idx] = e.target.value;
                  onChange(next);
                }}
              />
              <button
                type="button"
                onClick={() => {
                  const next = [...items];
                  next.splice(idx, 1);
                  onChange(next);
                }}
                className="p-2 mt-1 text-slate-400 hover:text-red-500 transition-colors rounded hover:bg-red-50"
              >
                &times;
              </button>
            </div>
          ))}
          <Button
            variant="outline"
            onClick={() => onChange([...items, ""])}
            className="w-full border-dashed text-teal-600"
          >
            + Tambah {label}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function PlainList({
  items,
  placeholder,
  onChange,
  addLabel,
}: {
  items: string[];
  placeholder: string;
  onChange: (items: string[]) => void;
  addLabel: string;
}) {
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="flex gap-2 items-start">
          <textarea
            className="flex-1 min-h-[60px] p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50"
            value={item}
            placeholder={placeholder}
            onChange={(e) => {
              const next = [...items];
              next[idx] = e.target.value;
              onChange(next);
            }}
          />
          <button
            type="button"
            onClick={() => {
              const next = [...items];
              next.splice(idx, 1);
              onChange(next);
            }}
            className="p-2 mt-1 text-slate-400 hover:text-red-500 transition-colors rounded hover:bg-red-50"
          >
            &times;
          </button>
        </div>
      ))}
      <Button
        variant="outline"
        onClick={() => onChange([...items, ""])}
        className="w-full border-dashed text-teal-600"
      >
        {addLabel}
      </Button>
    </div>
  );
}

function AiOverlay({ step }: { step: number }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md mx-4 p-10 flex flex-col items-center gap-8">
        <div className="relative flex items-center justify-center w-24 h-24">
          <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-teal-500 rounded-full border-t-transparent animate-spin"></div>
          <span className="text-3xl select-none">✨</span>
        </div>
        <div className="text-center space-y-1">
          <h3 className="text-xl font-semibold text-slate-800">
            AI Sedang Menyusun RPS
          </h3>
          <p className="text-sm text-slate-500">
            Proses ini memerlukan 1–2 menit. Harap jangan tutup halaman ini.
          </p>
        </div>
        <div className="w-full space-y-3">
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-teal-400 to-teal-600 rounded-full transition-all duration-1000"
              style={{ width: `${loadingSteps[step]?.pct ?? 10}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-400">
            <span className="animate-pulse font-medium text-teal-600">
              {loadingSteps[step]?.label}
            </span>
            <span>{loadingSteps[step]?.pct ?? 10}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AiModal({
  courseName,
  courseCode,
  description,
  links,
  onChangeCourseName,
  onChangeCourseCode,
  onChangeDescription,
  onChangeLinks,
  onPickPdf,
  onCancel,
  onSubmit,
}: {
  courseName: string;
  courseCode: string;
  description: string;
  links: string[];
  onChangeCourseName: (v: string) => void;
  onChangeCourseCode: (v: string) => void;
  onChangeDescription: (v: string) => void;
  onChangeLinks: (v: string[]) => void;
  onPickPdf: (file: File | null) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            ✨ Generate dengan AI
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            AI akan menyusun RPS lengkap berdasarkan informasi mata kuliah dan referensi yang Anda berikan. Field di bawah disinkronkan dengan form manual.
          </p>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">
                Nama Mata Kuliah
              </label>
              <input
                type="text"
                className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                value={courseName}
                onChange={(e) => onChangeCourseName(e.target.value)}
                placeholder="Cth: Aljabar"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">
                Kode
              </label>
              <input
                type="text"
                className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                value={courseCode}
                onChange={(e) => onChangeCourseCode(e.target.value)}
                placeholder="MA101"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">
              Deskripsi / Konteks (Opsional)
            </label>
            <textarea
              className="w-full p-2 border rounded-lg text-sm bg-slate-50 min-h-[60px]"
              placeholder="Topik yang ingin difokuskan..."
              value={description}
              onChange={(e) => onChangeDescription(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">
              Referensi PDF (Silabus lama, dll)
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) =>
                onPickPdf(e.target.files ? e.target.files[0] : null)
              }
              className="w-full p-2 border rounded-lg text-sm bg-slate-50"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">
              Tautan Jurnal / Referensi
            </label>
            {links.map((link, idx) => (
              <div key={idx} className="flex gap-2 mb-2">
                <input
                  type="url"
                  value={link}
                  onChange={(e) => {
                    const nl = [...links];
                    nl[idx] = e.target.value;
                    onChangeLinks(nl);
                  }}
                  className="flex-1 p-2 border rounded-lg text-sm bg-slate-50"
                  placeholder="https://..."
                />
              </div>
            ))}
            <button
              type="button"
              onClick={() => onChangeLinks([...links, ""])}
              className="text-xs text-indigo-600 font-medium"
            >
              + Tambah Link
            </button>
          </div>
        </div>
        <div className="flex gap-3 justify-end pt-4 border-t">
          <Button variant="outline" onClick={onCancel}>
            Batal
          </Button>
          <Button
            onClick={onSubmit}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            Mulai Generate
          </Button>
        </div>
      </div>
    </div>
  );
}

function MeetingRow({
  meeting,
  bahanKajianOptions,
  cpmkList,
  referencesList,
  metodeOptions,
  evaluasiOptions,
  onChange,
}: {
  meeting: RpsMeeting;
  bahanKajianOptions: string[];
  cpmkList: string[];
  referencesList: string[];
  metodeOptions: string[];
  evaluasiOptions: string[];
  onChange: (next: RpsMeeting) => void;
}) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const exam = isExamWeek(meeting.week);

  // Lock UTS / UAS rows: render a read-only banner instead of the inputs.
  if (exam) {
    return (
      <div className="flex items-center gap-4 border border-rose-100 bg-rose-50/40 rounded-xl p-4">
        <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-rose-100 text-rose-700 font-bold text-lg shrink-0">
          M{meeting.week}
        </div>
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wide text-rose-500 font-semibold">
            Modul Ujian
          </p>
          <p className="italic text-slate-700">{examTitleFor(meeting.week)}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Modul ini terkunci sesuai template institusi.
          </p>
        </div>
      </div>
    );
  }

  // Build label maps for the option lists
  const cpmkLabels = cpmkList.map((c, i) => `${i + 1}. ${(c || "").slice(0, 80)}`);

  return (
    <div className="flex flex-col md:flex-row gap-4 items-start border border-slate-100 rounded-xl p-5 bg-white shadow-sm hover:border-slate-200 transition-colors">
      <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-teal-50 text-teal-700 font-bold text-lg shrink-0">
        M{meeting.week}
      </div>
      <div className="flex-1 space-y-4 w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1.5 block">
              Bahan Kajian/Topik
            </label>
            <select
              className="w-full p-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50 disabled:opacity-50"
              value={meeting.bahan_kajian_topik}
              disabled={bahanKajianOptions.length === 0}
              onChange={(e) =>
                onChange({ ...meeting, bahan_kajian_topik: e.target.value })
              }
            >
              <option value="">— Pilih Bahan Kajian —</option>
              {bahanKajianOptions
                .filter((b) => b && b.trim() !== "")
                .map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
            </select>
            {bahanKajianOptions.length === 0 && (
              <p className="text-[11px] text-amber-600 mt-1">
                Tambahkan dulu Bahan Kajian di kartu di atas.
              </p>
            )}
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1.5 block">
              CPMK Terkait
            </label>
            <select
              className="w-full p-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50 disabled:opacity-50"
              value={meeting.cpmk_number ?? ""}
              disabled={cpmkList.length === 0}
              onChange={(e) =>
                onChange({
                  ...meeting,
                  cpmk_number: e.target.value === "" ? null : Number(e.target.value),
                })
              }
            >
              <option value="">— Pilih nomor CPMK —</option>
              {cpmkLabels.map((label, i) => (
                <option key={i + 1} value={i + 1}>
                  {label}
                </option>
              ))}
            </select>
            {cpmkList.length === 0 && (
              <p className="text-[11px] text-amber-600 mt-1">
                Tambahkan dulu CPMK di kartu di atas.
              </p>
            )}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 mb-1.5 block">
            Sub-Topik (Judul)
          </label>
          <input
            type="text"
            className="w-full p-2.5 border border-slate-200 rounded-lg text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 bg-slate-50 focus:bg-white transition-colors"
            value={meeting.sub_topic_title}
            placeholder="Contoh: Pengantar AI Terapan dan Agentic AI"
            onChange={(e) =>
              onChange({ ...meeting, sub_topic_title: e.target.value })
            }
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 mb-1.5 block">
            Sub-Topik (Deskripsi)
          </label>
          <textarea
            className="w-full min-h-[60px] p-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50"
            value={meeting.sub_topic_description}
            placeholder="Contoh: Peran AI dalam sistem bisnis dan layanan TI; pergeseran AI sebagai tool ke AI sebagai agent."
            onChange={(e) =>
              onChange({ ...meeting, sub_topic_description: e.target.value })
            }
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 mb-1.5 block">
            No. Referensi
          </label>
          {referencesList.length === 0 ? (
            <p className="text-[11px] text-amber-600">
              Tambahkan dulu Referensi & Pustaka di atas.
            </p>
          ) : (
            <ReferenceIndexPicker
              referencesList={referencesList}
              value={meeting.reference_indices || []}
              onChange={(indices) =>
                onChange({ ...meeting, reference_indices: indices })
              }
            />
          )}
        </div>

        <div>
          <button
            type="button"
            onClick={() => setAdvancedOpen((v) => !v)}
            className="text-[11px] text-slate-500 hover:text-slate-700 underline-offset-2 hover:underline"
          >
            {advancedOpen ? "▾ Sembunyikan" : "▸ Tampilkan"} kolom internal (Metode & Evaluasi)
          </button>
          {advancedOpen && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Metode Pembelajaran (internal)
                </label>
                <MultiSelect
                  options={metodeOptions}
                  value={meeting.method}
                  placeholder="Pilih metode..."
                  onChange={(val) => onChange({ ...meeting, method: val })}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 mb-1.5 block">
                  Evaluasi (internal)
                </label>
                <MultiSelect
                  options={evaluasiOptions}
                  value={meeting.evaluation}
                  placeholder="Pilih evaluasi..."
                  onChange={(val) => onChange({ ...meeting, evaluation: val })}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * References editor that surfaces 1-based numbering and reports an
 * `oldIndex -> newIndex | null` map on every mutation so meeting
 * `reference_indices` stay aligned with the cited reference text.
 */
function NumberedReferencesEditor({
  items,
  onMutate,
}: {
  items: string[];
  onMutate: (next: string[], indexRemap: Record<number, number | null>) => void;
}) {
  const safeItems = items.length > 0 ? items : [""];

  const buildRemap = (
    nextIndexFor: (oldOneBased: number) => number | null
  ): Record<number, number | null> => {
    const remap: Record<number, number | null> = {};
    safeItems.forEach((_, i) => {
      remap[i + 1] = nextIndexFor(i + 1);
    });
    return remap;
  };

  const updateAt = (idx: number, value: string) => {
    const next = [...safeItems];
    next[idx] = value;
    // Identity remap — same indices, just text edited.
    onMutate(next, buildRemap((n) => n));
  };

  const removeAt = (idx: number) => {
    if (!confirm(`Hapus referensi nomor ${idx + 1}? Semua kutipan ke nomor ini di tabel pertemuan akan dilepas.`)) {
      return;
    }
    const next = safeItems.filter((_, i) => i !== idx);
    onMutate(
      next.length > 0 ? next : [""],
      buildRemap((n) =>
        n - 1 === idx ? null : n - 1 < idx ? n : n - 1
      )
    );
  };

  const moveUp = (idx: number) => {
    if (idx === 0) return;
    const next = [...safeItems];
    [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
    onMutate(
      next,
      buildRemap((n) =>
        n === idx ? n + 1 : n === idx + 1 ? n - 1 : n
      )
    );
  };

  const moveDown = (idx: number) => {
    if (idx >= safeItems.length - 1) return;
    const next = [...safeItems];
    [next[idx], next[idx + 1]] = [next[idx + 1], next[idx]];
    onMutate(
      next,
      buildRemap((n) =>
        n === idx + 1 ? n + 1 : n === idx + 2 ? n - 1 : n
      )
    );
  };

  const addEntry = () => {
    onMutate([...safeItems, ""], buildRemap((n) => n));
  };

  return (
    <div className="space-y-3">
      {safeItems.map((item, idx) => (
        <div key={idx} className="flex gap-2 items-start">
          <span className="inline-flex items-center justify-center min-w-[28px] h-9 px-2 mt-1 rounded-md bg-teal-50 text-teal-700 text-xs font-semibold">
            {idx + 1}.
          </span>
          <textarea
            className="flex-1 min-h-[60px] p-3 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/50"
            value={item}
            placeholder='Contoh: "Stuart Russell - Artificial Intelligence: A Modern Approach (4th ed.)"'
            onChange={(e) => updateAt(idx, e.target.value)}
          />
          <div className="flex flex-col gap-1 mt-1">
            <button
              type="button"
              title="Naik"
              onClick={() => moveUp(idx)}
              disabled={idx === 0}
              className="px-2 py-0.5 text-xs text-slate-500 hover:text-slate-800 disabled:opacity-30"
            >
              ▲
            </button>
            <button
              type="button"
              title="Turun"
              onClick={() => moveDown(idx)}
              disabled={idx >= safeItems.length - 1}
              className="px-2 py-0.5 text-xs text-slate-500 hover:text-slate-800 disabled:opacity-30"
            >
              ▼
            </button>
          </div>
          <button
            type="button"
            onClick={() => removeAt(idx)}
            className="p-2 mt-1 text-slate-400 hover:text-red-500 transition-colors rounded hover:bg-red-50"
          >
            &times;
          </button>
        </div>
      ))}
      <Button
        variant="outline"
        onClick={addEntry}
        className="w-full border-dashed text-teal-600"
      >
        + Tambah Referensi
      </Button>
    </div>
  );
}

/**
 * Multi-select picker for per-meeting reference indices.
 *
 * Operates on `number[]` directly so reference text containing commas
 * (e.g. "Russell, Stuart, dan Peter Norvig...") doesn't get split into
 * separate chips like the generic `MultiSelect` would do.
 */
function ReferenceIndexPicker({
  referencesList,
  value,
  onChange,
}: {
  referencesList: string[];
  value: number[];
  onChange: (next: number[]) => void;
}) {
  const [open, setOpen] = useState(false);

  const toggle = (idx: number) => {
    if (value.includes(idx)) {
      onChange(value.filter((v) => v !== idx));
    } else {
      onChange([...value, idx].sort((a, b) => a - b));
    }
  };

  return (
    <div className="relative">
      <div
        className="w-full min-h-[42px] p-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white flex flex-wrap gap-1 cursor-pointer items-center"
        onClick={() => setOpen((v) => !v)}
      >
        {value.length === 0 && (
          <span className="text-slate-400 p-1">
            Pilih nomor referensi (boleh lebih dari satu)...
          </span>
        )}
        {value.map((idx) => {
          const text = referencesList[idx - 1] ?? "(referensi hilang)";
          return (
            <span
              key={idx}
              title={text}
              className="bg-teal-100 text-teal-800 px-2 py-0.5 rounded text-xs flex items-center gap-1 shadow-sm max-w-[260px]"
            >
              <span className="font-semibold">{idx}.</span>
              <span className="truncate">{text}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggle(idx);
                }}
                className="text-teal-600 hover:text-teal-900 shrink-0"
              >
                &times;
              </button>
            </span>
          );
        })}
      </div>
      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          ></div>
          <div className="absolute z-20 w-full mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-64 overflow-y-auto">
            {referencesList.map((ref, i) => {
              const idx = i + 1;
              const checked = value.includes(idx);
              return (
                <div
                  key={idx}
                  className="px-3 py-2 text-sm hover:bg-slate-50 cursor-pointer flex items-start gap-2 border-b border-slate-50 last:border-0"
                  onClick={() => toggle(idx)}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    readOnly
                    className="rounded text-teal-600 focus:ring-teal-500 mt-0.5"
                  />
                  <span
                    className={
                      checked
                        ? "font-medium text-teal-700"
                        : "text-slate-700"
                    }
                  >
                    <span className="font-semibold mr-1">{idx}.</span>
                    {ref || "(kosong)"}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
