import Link from "next/link";
import { revalidatePath } from "next/cache";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { apiFetch, apiUrl } from "@/lib/api";

async function publishQuiz(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await fetch(apiUrl(`/api/quiz/publish/${id}`), { method: "POST" });
  revalidatePath("/dashboard/quiz");
}

async function closeQuiz(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await fetch(apiUrl(`/api/quiz/close/${id}`), { method: "POST" });
  revalidatePath("/dashboard/quiz");
}

async function deleteQuiz(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await fetch(apiUrl(`/api/quiz/${id}`), { method: "DELETE" });
  revalidatePath("/dashboard/quiz");
}

export default async function QuizAssessment() {
  const data = await apiFetch<any>("/api/dashboard/quizzes");

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">📝 Kuis & Evaluasi Mahasiswa</h1>
          <p className="mt-1 text-sm text-slate-500">
            Buat kuis manual atau dengan AI, pantau pengerjaan, dan jalankan auto-grading.
          </p>
        </div>
        <Link href="/dashboard/quiz/new">
          <Button>+ Buat Kuis</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {data.summary.map((item: any) => (
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Kuis Sedang Berjalan</CardTitle>
            <CardDescription>
              Pantau progres pengerjaan mahasiswa.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.active.length === 0 && (
              <p className="text-sm text-slate-500">Tidak ada kuis aktif saat ini.</p>
            )}
            {data.active.map((quiz: any) => (
              <div
                key={quiz.id}
                className="rounded-2xl border border-slate-200/70 bg-white p-4"
              >
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-base font-semibold text-slate-900">
                      {quiz.title}
                    </p>
                    <p className="text-sm text-slate-500">
                      {quiz.course} • {quiz.details}
                    </p>
                  </div>
                  <Badge variant="outline">{quiz.time_left} lagi</Badge>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Dikerjakan {quiz.submissions}/{quiz.total_students} mahasiswa
                    </span>
                    <span>{quiz.progress_percent}%</span>
                  </div>
                  <Progress
                    value={quiz.progress_percent}
                    colorClassName="bg-teal-500"
                  />
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <Link href={`/dashboard/quiz/${quiz.id}`}>
                    <Button size="sm" variant="secondary">
                      Lihat Detail & Grading
                    </Button>
                  </Link>
                  <form action={closeQuiz}>
                    <input type="hidden" name="id" value={quiz.id} />
                    <Button size="sm" variant="outline" type="submit">
                      Tutup Kuis
                    </Button>
                  </form>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Kuis Selesai — Perlu Remedial</CardTitle>
            <CardDescription>
              Kuis dengan nilai di bawah batas lulus.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.needs_attention.length === 0 && (
              <p className="text-sm text-slate-500">Semua kelas baik-baik saja.</p>
            )}
            {data.needs_attention.map((item: any) => (
              <div
                key={item.id}
                className="rounded-2xl border border-rose-200 bg-rose-50 p-4"
              >
                <p className="text-sm font-semibold text-rose-800">
                  {item.title}
                </p>
                <p className="mt-1 text-xs text-rose-700">{item.issue}</p>
                <Link href={`/dashboard/quiz/${item.id}`} className="mt-3 inline-block">
                  <Button size="sm" variant="outline">
                    Lihat Hasil Detail
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Draft Kuis</CardTitle>
          <CardDescription>
            Tinjau draft sebelum dipublikasikan ke mahasiswa.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.draft.length === 0 && (
            <p className="text-sm text-slate-500">Belum ada draft kuis.</p>
          )}
          {data.draft.map((draft: any) => (
            <div
              key={draft.id}
              className="rounded-2xl border border-slate-200/70 bg-white p-4"
            >
              <p className="text-sm font-semibold text-slate-900">
                {draft.title}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {draft.course} • {draft.questions} soal
              </p>
              <div className="mt-4 flex gap-2">
                <Link href={`/dashboard/quiz/${draft.id}`}>
                  <Button size="sm" variant="secondary">
                    Lanjutkan
                  </Button>
                </Link>
                <form action={publishQuiz}>
                  <input type="hidden" name="id" value={draft.id} />
                  <Button type="submit" size="sm" variant="outline">
                    Publikasi
                  </Button>
                </form>
                <form action={deleteQuiz} className="ml-auto">
                  <input type="hidden" name="id" value={draft.id} />
                  <Button type="submit" size="sm" variant="ghost" className="text-rose-600">
                    Hapus
                  </Button>
                </form>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
