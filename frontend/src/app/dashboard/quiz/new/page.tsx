"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";
import { KnowledgeMaterialPicker } from "./KnowledgeMaterialPicker";

type Course = {
  id: string;
  name: string;
  code: string;
};

type QuizCfg = {
  course_id: string;
  week_number: number;
  quiz_type: "multiple_choice" | "essay" | "mixed";
  difficulty_level: "easy" | "medium" | "hard" | "adaptive";
  num_questions: number;
  title: string;
};

type ManualQuestion = {
  id: string;
  type: "multiple_choice" | "essay";
  question: string;
  options?: { A: string; B: string; C: string; D: string };
  correct_answer?: string;
  rubric?: { excellent: string; good: string; satisfactory: string };
};

const blankCfg = (): QuizCfg => ({
  course_id: "",
  week_number: 1,
  quiz_type: "mixed",
  difficulty_level: "medium",
  num_questions: 5,
  title: "",
});

const blankMcq = (idx: number): ManualQuestion => ({
  id: `Q${String(idx + 1).padStart(3, "0")}`,
  type: "multiple_choice",
  question: "",
  options: { A: "", B: "", C: "", D: "" },
  correct_answer: "A",
});

const blankEssay = (idx: number): ManualQuestion => ({
  id: `Q${String(idx + 1).padStart(3, "0")}`,
  type: "essay",
  question: "",
  rubric: { excellent: "", good: "", satisfactory: "" },
});

function NewQuizContent() {
  const router = useRouter();
  const search = useSearchParams();
  const initialCourseId = search.get("course_id") ?? "";
  const initialMode = search.get("mode") === "ai" ? "ai" : "manual";

  const [tab, setTab] = useState<"manual" | "ai">(initialMode);
  const [courses, setCourses] = useState<Course[]>([]);
  const [cfg, setCfg] = useState<QuizCfg>({
    ...blankCfg(),
    course_id: initialCourseId,
  });
  const [aiMaterial, setAiMaterial] = useState("");
  const [questions, setQuestions] = useState<ManualQuestion[]>([blankMcq(0)]);
  const [loading, setLoading] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  useEffect(() => {
    apiFetch<Course[]>("/api/courses/")
      .then((cs) => {
        setCourses(cs);
        if (!cfg.course_id && cs.length > 0) {
          setCfg((c) => ({ ...c, course_id: cs[0].id }));
        }
      })
      .catch((e) => console.error("Failed to load courses", e));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateCfg = <K extends keyof QuizCfg>(key: K, value: QuizCfg[K]) => {
    setCfg((c) => ({ ...c, [key]: value }));
  };

  const handleManualSave = async () => {
    if (!cfg.course_id) {
      alert("Pilih mata kuliah terlebih dahulu.");
      return;
    }
    if (questions.length === 0) {
      alert("Tambahkan minimal satu soal.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch<{ data: { quiz_id: string } }>(`/api/quiz/`, {
        method: "POST",
        json: { ...cfg, questions },
      });
      router.push(`/dashboard/quiz/${res.data.quiz_id}`);
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan kuis: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAiGenerate = async () => {
    if (!cfg.course_id) {
      alert("Pilih mata kuliah terlebih dahulu.");
      return;
    }
    if (!aiMaterial.trim()) {
      alert("Materi acuan tidak boleh kosong untuk mode AI.");
      return;
    }
    setLoading(true);
    try {
      const data = await apiFetch<any>(`/api/quiz/generate`, {
        method: "POST",
        json: { ...cfg, material_content: aiMaterial },
      });
      setAiResult(data);
    } catch (e: any) {
      alert(`Gagal generate kuis: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (aiResult) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto">
        <Card className="border-teal-500 shadow-md">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-600">
                ✓
              </div>
              <div>
                <CardTitle>Kuis Berhasil Dibuat</CardTitle>
                <CardDescription>
                  AI telah menghasilkan draft kuis dan menyimpannya ke daftar.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {aiResult?.data?.questions?.map((q: any, i: number) => (
              <div
                key={q.id}
                className="p-4 bg-slate-50 rounded-lg space-y-3 border border-slate-200"
              >
                <div className="flex items-center justify-between">
                  <Badge variant={q.type === "essay" ? "warning" : "outline"}>
                    {q.type === "essay" ? "Esai" : "Pilihan Ganda"}
                  </Badge>
                  <span className="text-xs text-slate-500 font-medium">
                    Bloom: {q.bloom_level}
                  </span>
                </div>
                <p className="font-medium text-slate-800">
                  {i + 1}. {q.question}
                </p>
                {q.type === "multiple_choice" && q.options && (
                  <div className="space-y-1 pl-4">
                    {Object.entries(q.options).map(([key, val]: any) => (
                      <div
                        key={key}
                        className={`text-sm p-2 rounded ${
                          key === q.correct_answer
                            ? "bg-green-100 text-green-800 font-medium"
                            : "text-slate-600"
                        }`}
                      >
                        {key}. {val}
                      </div>
                    ))}
                  </div>
                )}
                {q.type === "essay" && q.rubric && (
                  <div className="mt-2 bg-white p-3 rounded border text-sm text-slate-600">
                    <p className="font-semibold text-slate-800 mb-1">
                      Rubric:
                    </p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li>
                        <strong>Excellent:</strong> {q.rubric.excellent}
                      </li>
                      <li>
                        <strong>Good:</strong> {q.rubric.good}
                      </li>
                      <li>
                        <strong>Satisfactory:</strong> {q.rubric.satisfactory}
                      </li>
                    </ul>
                  </div>
                )}
              </div>
            ))}
            <div className="flex gap-3 justify-end pt-4 border-t border-slate-100">
              <Button variant="outline" onClick={() => setAiResult(null)}>
                Buat Ulang
              </Button>
              <Link href="/dashboard/quiz">
                <Button className="bg-teal-600 hover:bg-teal-700">
                  Selesai
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Buat Kuis</h1>
          <p className="mt-1 text-sm text-slate-500">
            Susun kuis manual atau biarkan AI menyusunnya dari materi acuan.
          </p>
        </div>
        <Link href="/dashboard/quiz">
          <Button variant="outline">Batal</Button>
        </Link>
      </div>

      <div className="flex gap-2 border-b border-slate-200">
        <TabButton
          active={tab === "manual"}
          onClick={() => setTab("manual")}
          label="✏️ Manual"
        />
        <TabButton
          active={tab === "ai"}
          onClick={() => setTab("ai")}
          label="✨ Generate dengan AI"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Konfigurasi Kuis</CardTitle>
          <CardDescription>
            Field di bawah dipakai sama persis baik untuk pembuatan manual maupun AI.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Mata Kuliah</label>
              <select
                value={cfg.course_id}
                onChange={(e) => updateCfg("course_id", e.target.value)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="">Pilih mata kuliah...</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Judul Kuis (Opsional)</label>
              <input
                type="text"
                value={cfg.title}
                onChange={(e) => updateCfg("title", e.target.value)}
                placeholder="Contoh: Kuis Sorting Algorithm"
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Minggu Ke-</label>
                <input
                  type="number"
                  min={1}
                  max={16}
                  value={cfg.week_number}
                  onChange={(e) =>
                    updateCfg("week_number", parseInt(e.target.value) || 1)
                  }
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Jumlah Soal</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={cfg.num_questions}
                  onChange={(e) =>
                    updateCfg("num_questions", parseInt(e.target.value) || 1)
                  }
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Tipe Kuis</label>
                <select
                  value={cfg.quiz_type}
                  onChange={(e) =>
                    updateCfg("quiz_type", e.target.value as QuizCfg["quiz_type"])
                  }
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                >
                  <option value="multiple_choice">Pilihan Ganda</option>
                  <option value="essay">Esai</option>
                  <option value="mixed">Campuran</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tingkat Kesulitan</label>
                <select
                  value={cfg.difficulty_level}
                  onChange={(e) =>
                    updateCfg(
                      "difficulty_level",
                      e.target.value as QuizCfg["difficulty_level"]
                    )
                  }
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                >
                  <option value="easy">Mudah (LOTS)</option>
                  <option value="medium">Sedang (MOTS)</option>
                  <option value="hard">Sulit (HOTS)</option>
                  <option value="adaptive">Adaptif</option>
                </select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {tab === "ai" ? (
        <Card>
          <CardHeader>
            <CardTitle>Materi Acuan untuk AI</CardTitle>
            <CardDescription>
              Pilih dari Knowledge Hub atau paste teks materi langsung. Anda juga bisa upload PDF baru di sini — file tersimpan ke Knowledge Hub.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <KnowledgeMaterialPicker
              courseId={cfg.course_id}
              onUseMaterial={(text) =>
                setAiMaterial((prev) =>
                  prev.trim() ? `${prev}\n\n${text}` : text
                )
              }
            />
            <textarea
              value={aiMaterial}
              onChange={(e) => setAiMaterial(e.target.value)}
              className="w-full min-h-[260px] rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Atau paste teks materi langsung di sini..."
            />
            <div className="flex justify-end">
              <Button
                onClick={handleAiGenerate}
                disabled={loading}
                className="bg-teal-600 hover:bg-teal-700"
              >
                {loading ? "AI sedang menyusun soal..." : "Generate Kuis"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Daftar Soal</CardTitle>
                <CardDescription>
                  Tambahkan soal pilihan ganda atau esai sesuai konfigurasi di atas.
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setQuestions((qs) => [...qs, blankMcq(qs.length)])
                  }
                >
                  + MCQ
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setQuestions((qs) => [...qs, blankEssay(qs.length)])
                  }
                >
                  + Esai
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            {questions.map((q, idx) => (
              <ManualQuestionCard
                key={q.id}
                index={idx}
                value={q}
                onChange={(next) =>
                  setQuestions((qs) => qs.map((x, i) => (i === idx ? next : x)))
                }
                onRemove={() =>
                  setQuestions((qs) => qs.filter((_, i) => i !== idx))
                }
              />
            ))}
            <div className="flex justify-end">
              <Button
                onClick={handleManualSave}
                disabled={loading}
                className="bg-teal-600 hover:bg-teal-700"
              >
                {loading ? "Menyimpan..." : "Simpan Draft Kuis"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function NewQuizPage() {
  return (
    <Suspense fallback={<div className="p-8">Memuat…</div>}>
      <NewQuizContent />
    </Suspense>
  );
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
        active
          ? "border-teal-600 text-teal-700"
          : "border-transparent text-slate-500 hover:text-slate-700"
      }`}
    >
      {label}
    </button>
  );
}

function ManualQuestionCard({
  index,
  value,
  onChange,
  onRemove,
}: {
  index: number;
  value: ManualQuestion;
  onChange: (next: ManualQuestion) => void;
  onRemove: () => void;
}) {
  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700">
            Soal {index + 1}
          </span>
          <Badge variant={value.type === "essay" ? "warning" : "outline"}>
            {value.type === "essay" ? "Esai" : "Pilihan Ganda"}
          </Badge>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="text-rose-500 text-sm hover:underline"
        >
          Hapus
        </button>
      </div>

      <textarea
        value={value.question}
        onChange={(e) => onChange({ ...value, question: e.target.value })}
        className="w-full min-h-[80px] p-3 border border-slate-200 rounded-lg text-sm bg-slate-50"
        placeholder="Tulis pertanyaan..."
      />

      {value.type === "multiple_choice" && value.options && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(["A", "B", "C", "D"] as const).map((key) => (
            <div key={key} className="flex gap-2 items-start">
              <label className="mt-2 text-sm font-medium w-6">{key}.</label>
              <input
                type="text"
                value={value.options![key]}
                onChange={(e) =>
                  onChange({
                    ...value,
                    options: { ...value.options!, [key]: e.target.value },
                  })
                }
                className="flex-1 p-2 border rounded-lg text-sm bg-slate-50"
                placeholder={`Opsi ${key}`}
              />
            </div>
          ))}
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-slate-500 mb-1 block">
              Jawaban Benar
            </label>
            <select
              value={value.correct_answer || "A"}
              onChange={(e) =>
                onChange({ ...value, correct_answer: e.target.value })
              }
              className="h-9 w-full md:w-32 rounded-md border border-slate-300 bg-white px-3 text-sm"
            >
              {["A", "B", "C", "D"].map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {value.type === "essay" && value.rubric && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(["excellent", "good", "satisfactory"] as const).map((k) => (
            <div key={k}>
              <label className="text-xs font-medium text-slate-500 mb-1 block capitalize">
                Rubric {k}
              </label>
              <textarea
                value={value.rubric![k]}
                onChange={(e) =>
                  onChange({
                    ...value,
                    rubric: { ...value.rubric!, [k]: e.target.value },
                  })
                }
                className="w-full min-h-[60px] p-2 border rounded-lg text-sm bg-slate-50"
                placeholder={`Kriteria ${k}`}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
