"use client";

import { useEffect, useState, use } from "react";
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
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

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

export default function EditQuizPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const resolved = use(params);
  const quizId = resolved.id;

  const [courses, setCourses] = useState<Course[]>([]);
  const [cfg, setCfg] = useState<QuizCfg | null>(null);
  const [questions, setQuestions] = useState<ManualQuestion[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<Course[]>("/api/courses/")
      .then((cs) => setCourses(cs))
      .catch((e) => console.error("Failed to load courses", e));

    apiFetch<any>(`/api/quiz/${quizId}`)
      .then((quiz) => {
        setCfg({
          course_id: quiz.course_id,
          week_number: quiz.week_number || 1,
          quiz_type: "mixed", // fallback
          difficulty_level: "medium", // fallback
          num_questions: quiz.questions?.length || 0,
          title: quiz.title || "",
        });

        // Reconstruct full questions state including correct answers and rubrics from answer_key
        const qList = (quiz.questions || []).map((q: any) => {
          const ans = quiz.answer_key?.find((a: any) => a.id === q.id)?.answer;
          if (q.type === "essay") {
            return {
              ...q,
              rubric: ans || { excellent: "", good: "", satisfactory: "" },
            };
          } else {
            return {
              ...q,
              correct_answer: ans || "A",
              options: q.options || { A: "", B: "", C: "", D: "" },
            };
          }
        });
        setQuestions(qList);
      })
      .catch((e) => console.error("Failed to load quiz", e));
  }, [quizId]);

  const updateCfg = <K extends keyof QuizCfg>(key: K, value: QuizCfg[K]) => {
    if (cfg) {
      setCfg({ ...cfg, [key]: value });
    }
  };

  const handleSave = async () => {
    if (!cfg?.course_id) {
      alert("Pilih mata kuliah terlebih dahulu.");
      return;
    }
    if (questions.length === 0) {
      alert("Tambahkan minimal satu soal.");
      return;
    }
    setLoading(true);
    try {
      await apiFetch(`/api/quiz/${quizId}`, {
        method: "PUT",
        json: { ...cfg, questions },
      });
      router.push(`/dashboard/quiz/${quizId}`);
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan kuis: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!cfg) return <div className="p-8">Memuat data kuis...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Edit Kuis</h1>
          <p className="mt-1 text-sm text-slate-500">
            Edit soal dan konfigurasi kuis Anda.
          </p>
        </div>
        <Link href={`/dashboard/quiz/${quizId}`}>
          <Button variant="outline">Batal</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Konfigurasi Kuis</CardTitle>
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
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Daftar Soal</CardTitle>
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
              key={q.id || idx}
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
              onClick={handleSave}
              disabled={loading}
              className="bg-teal-600 hover:bg-teal-700"
            >
              {loading ? "Menyimpan..." : "Simpan Kuis"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
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
                value={value.options![key] || ""}
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
                value={value.rubric![k as keyof typeof value.rubric] || ""}
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
