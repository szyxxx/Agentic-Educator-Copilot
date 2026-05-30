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
import Submissions from "./Submissions";

type Submission = {
  id: string;
  nim: string;
  name: string;
  answered_count: number;
  status: "submitted" | "graded" | "unmatched";
  score: number | null;
  feedback: string | null;
};

export default function QuizDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const resolved = use(params);
  const quizId = resolved.id;

  const [quiz, setQuiz] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [grading, setGrading] = useState(false);
  const [gradingResult, setGradingResult] = useState<any>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [expandedFeedback, setExpandedFeedback] = useState<string | null>(null);

  const loadQuiz = () =>
    apiFetch<any>(`/api/quiz/${quizId}`)
      .then(setQuiz)
      .catch((e) => console.error(e));

  const loadSubmissions = async () => {
    try {
      const data = await apiFetch<Submission[]>(`/api/quiz/${quizId}/submissions`);
      setSubmissions(data);
    } catch (_) {}
  };

  useEffect(() => {
    loadQuiz();
    loadSubmissions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizId]);

  const publish = async () => {
    setLoading(true);
    try {
      await apiFetch(`/api/quiz/publish/${quizId}`, { method: "POST" });
      await loadQuiz();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const runGrading = async () => {
    setGrading(true);
    try {
      const res = await apiFetch<any>(`/api/grading/run/${quizId}`, {
        method: "POST",
      });
      setGradingResult(res.data);
      await loadSubmissions();
      await loadQuiz();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setGrading(false);
    }
  };

  if (!quiz) {
    return <div className="p-8">Memuat data kuis...</div>;
  }

  // Derive grading summary from submissions (survives page refresh)
  const gradedSubs = submissions.filter((s) => s.status === "graded" && s.score !== null);
  const hasGradedData = gradedSubs.length > 0;
  const derivedAvg =
    hasGradedData
      ? Math.round((gradedSubs.reduce((sum, s) => sum + (s.score ?? 0), 0) / gradedSubs.length) * 10) / 10
      : null;

  // Use live gradingResult (from just-run grading) or fall back to derived data
  const showGradingPanel = !!gradingResult || hasGradedData;

  const isGradable = quiz.status === "active" || quiz.status === "completed" || quiz.status === "attention";

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
            Detail Kuis
          </p>
          <h1 className="text-3xl font-semibold">{quiz.title}</h1>
          <p className="mt-1 text-sm text-slate-500">{quiz.details}</p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/quiz">
            <Button variant="outline">Kembali</Button>
          </Link>
          {quiz.status === "draft" && (
            <>
              <Link href={`/dashboard/quiz/${quizId}/edit`}>
                <Button variant="outline" className="mr-2">Edit</Button>
              </Link>
              <Button
                onClick={publish}
                disabled={loading}
                className="bg-teal-600 hover:bg-teal-700"
              >
                {loading ? "Memproses..." : "Publikasi"}
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Stat label="Status" value={quiz.status} />
        <Stat
          label="Submission"
          value={`${quiz.submissions ?? 0}/${quiz.total_students ?? 0}`}
        />
        <Stat label="Progres" value={`${quiz.progress_percent ?? 0}%`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Soal</CardTitle>
          <CardDescription>
            Kunci jawaban hanya terlihat oleh dosen.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(quiz.questions || []).length === 0 && (
            <p className="text-sm text-slate-500">Belum ada soal.</p>
          )}
          {(quiz.questions || []).map((q: any, i: number) => (
            <div
              key={q.id ?? i}
              className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-3"
            >
              <div className="flex items-center justify-between">
                <Badge variant={q.type === "essay" ? "warning" : "outline"}>
                  {q.type === "essay" ? "Esai" : "Pilihan Ganda"}
                </Badge>
                {q.bloom_level && (
                  <span className="text-xs text-slate-500">
                    Bloom: {q.bloom_level}
                  </span>
                )}
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
                <div className="bg-white p-3 rounded border text-sm text-slate-600">
                  <p className="font-semibold text-slate-800 mb-1">Rubric:</p>
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
        </CardContent>
      </Card>

      <Submissions
        quizId={quizId}
        onChange={async () => {
          await loadQuiz();
          await loadSubmissions();
        }}
      />

      {/* AI Auto-Grading */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>AI Auto-Grading</CardTitle>
              <CardDescription>
                Jalankan agen AI untuk menilai jawaban yang sudah masuk.
              </CardDescription>
            </div>
            {hasGradedData && (
              <Badge variant="success">
                {gradedSubs.length} submission dinilai
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={runGrading}
            disabled={grading || quiz.status === "draft"}
            className="bg-teal-600 hover:bg-teal-700"
          >
            {grading
              ? "AI sedang menilai..."
              : quiz.status === "draft"
                ? "Publikasikan kuis dulu"
                : hasGradedData
                  ? "🔄 Jalankan Ulang Auto-Grading"
                  : "▶ Jalankan Auto-Grading"}
          </Button>

          {/* Summary panel — from live run OR derived from stored submissions */}
          {showGradingPanel && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Stat
                  label="Skor Rata-rata"
                  value={gradingResult?.total_score ?? derivedAvg ?? "-"}
                />
                <Stat
                  label="Topik Terlemah"
                  value={
                    (gradingResult?.weak_topics || []).join(", ") || "-"
                  }
                />
              </div>
              <div className="p-4 rounded-lg bg-teal-50 border border-teal-100 text-teal-900 text-sm">
                <strong>Feedback Kelas:</strong>{" "}
                {gradingResult?.overall_feedback ||
                  `${gradedSubs.length} submission sudah dinilai dengan skor rata-rata ${derivedAvg}.`}
              </div>
              {gradingResult?.auto_material_id && (
                <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-900 text-sm">
                  <strong>📚 Materi Otomatis:</strong> AI sudah menyiapkan materi
                  penguatan untuk Minggu {gradingResult.auto_material_week} dan
                  melampirkannya ke RPS. Buka tab RPS untuk meninjaunya.
                </div>
              )}

              {/* Per-student feedback accordion */}
              {gradedSubs.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <div className="bg-slate-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Hasil Per Mahasiswa
                  </div>
                  <div className="divide-y divide-slate-100">
                    {gradedSubs
                      .slice()
                      .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
                      .map((sub) => (
                        <div key={sub.id} className="px-4 py-3">
                          <button
                            className="w-full flex items-center justify-between text-left gap-4"
                            onClick={() =>
                              setExpandedFeedback(
                                expandedFeedback === sub.id ? null : sub.id
                              )
                            }
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="font-mono text-xs text-slate-400 shrink-0">
                                {sub.nim}
                              </span>
                              <span className="text-sm font-medium text-slate-800 truncate">
                                {sub.name}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span
                                className={`text-sm font-semibold tabular-nums ${
                                  (sub.score ?? 0) >= 75
                                    ? "text-emerald-600"
                                    : (sub.score ?? 0) >= 60
                                      ? "text-amber-600"
                                      : "text-rose-600"
                                }`}
                              >
                                {sub.score?.toFixed(1) ?? "-"}
                              </span>
                              <span className="text-slate-300 text-xs">
                                {expandedFeedback === sub.id ? "▲" : "▼"}
                              </span>
                            </div>
                          </button>
                          {expandedFeedback === sub.id && sub.feedback && (
                            <div className="mt-2 ml-1 pl-3 border-l-2 border-teal-200 text-sm text-slate-600">
                              {sub.feedback}
                            </div>
                          )}
                          {expandedFeedback === sub.id && !sub.feedback && (
                            <p className="mt-2 text-xs text-slate-400 italic">
                              Tidak ada feedback dari AI untuk submission ini.
                            </p>
                          )}
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-4 bg-slate-50 rounded-lg border">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
