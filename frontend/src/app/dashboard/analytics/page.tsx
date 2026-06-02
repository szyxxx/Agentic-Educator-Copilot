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
import { apiFetch, API_BASE } from "@/lib/api";

export default async function Analytics({
  searchParams,
}: {
  searchParams: Promise<{ course_id?: string }>;
}) {
  const params = await searchParams;
  const qs = params.course_id ? `?course_id=${params.course_id}` : "";
  const data = await apiFetch<any>(`/api/dashboard/analytics${qs}`);

  // Normalize trend bars so the tallest bar = 100% of container height
  const trend: { label: string; value: number }[] = data.trend || [];
  const maxTrend = trend.length > 0 ? Math.max(...trend.map((t) => t.value)) : 100;

  const perStudent: {
    nim: string;
    name: string;
    avg_score: number;
    status: "pass" | "fail";
  }[] = data.per_student || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">📈 Analitik Kelas</h1>
          <p className="mt-1 text-sm text-slate-500">
            {data.course_overview.course} • {data.course_overview.semester}
          </p>
        </div>
        <a href={`${API_BASE}/api/dashboard/analytics/export${qs}`} target="_blank" rel="noreferrer">
          <Button variant="secondary">Ekspor Laporan</Button>
        </a>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {data.kpis.map((item: any) => (
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Trend chart */}
        <Card>
          <CardHeader>
            <CardTitle>Tren Nilai per Kuis</CardTitle>
            <CardDescription>
              Rata-rata nilai kelas dari setiap kuis yang sudah dinilai.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {trend.length === 0 ? (
              <p className="text-sm text-slate-500">
                Belum ada nilai. Jalankan auto-grading untuk melihat tren.
              </p>
            ) : (
              <div className="flex h-40 items-end gap-3 pt-2">
                {trend.map((week) => {
                  const heightPct = maxTrend > 0 ? (week.value / maxTrend) * 100 : 0;
                  return (
                    <div
                      key={week.label}
                      className="group relative flex flex-1 flex-col items-center gap-1"
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full mb-1 hidden group-hover:block bg-slate-800 text-white text-[10px] rounded px-2 py-1 whitespace-nowrap z-10">
                        {week.label}: {week.value}
                      </div>
                      <div
                        className="w-full rounded-t-md bg-teal-500/80 transition-all hover:bg-teal-500"
                        style={{ height: `${heightPct}%`, minHeight: "4px" }}
                      />
                      <span className="text-xs text-slate-400 mt-1">{week.label}</span>
                      <span className="text-[10px] font-semibold text-slate-600">{week.value}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Distribusi Rentang Nilai</CardTitle>
            <CardDescription>
              Persentase peserta di tiap rentang nilai (A, B, C, D).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(data.distribution || []).length === 0 ? (
              <p className="text-sm text-slate-500">
                Belum ada submission yang dinilai.
              </p>
            ) : (
              (data.distribution || []).map((item: any) => (
                <div key={item.label} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">
                      {item.label}
                    </span>
                    <span className="text-slate-500">{item.value}</span>
                  </div>
                  <Progress value={item.percent} colorClassName={item.color} />
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* CPMK progress */}
        <Card>
          <CardHeader>
            <CardTitle>Pencapaian CPMK</CardTitle>
            <CardDescription>
              Progres ketercapaian tiap CPMK berdasarkan hasil kuis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(data.cpmk_progress || []).length === 0 ? (
              <p className="text-sm text-slate-500">
                Belum ada CPMK terdaftar pada RPS atau belum ada nilai.
              </p>
            ) : (
              (data.cpmk_progress || []).map((cpmk: any) => (
                <div key={cpmk.id} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700 truncate max-w-[70%]">
                      {cpmk.id}: {cpmk.title}
                    </span>
                    <Badge
                      variant={
                        cpmk.status === "good"
                          ? "success"
                          : cpmk.status === "warning"
                            ? "warning"
                            : "danger"
                      }
                    >
                      {cpmk.progress}%
                    </Badge>
                  </div>
                  <Progress
                    value={cpmk.progress}
                    colorClassName={
                      cpmk.status === "good"
                        ? "bg-emerald-500"
                        : cpmk.status === "warning"
                          ? "bg-amber-500"
                          : "bg-rose-500"
                    }
                  />
                </div>
              ))
            )}
            {data.insight && (
              <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-800">
                <span className="font-semibold">AI Insight:</span> {data.insight}
              </div>
            )}
          </CardContent>
        </Card>

        {/* At-risk heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>Mahasiswa Berisiko</CardTitle>
            <CardDescription>
              Deteksi dini mahasiswa dengan pola nilai menurun dalam pekan terakhir.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {(data.heatmap?.students || []).length === 0 ? (
              <p className="text-sm text-slate-500">
                Belum ada data submission untuk dianalisis.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="text-left text-slate-400">
                      <th className="pb-2">Nama</th>
                      {(data.heatmap?.weeks || []).map((week: string) => (
                        <th key={week} className="pb-2 text-center">
                          {week}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(data.heatmap?.students || []).map((student: any) => (
                      <tr key={student.nim ?? student.name}>
                        <td className="py-2 font-medium text-slate-700 pr-3">
                          <div>{student.name}</div>
                          {student.nim && (
                            <div className="text-[10px] text-slate-400 font-mono">{student.nim}</div>
                          )}
                        </td>
                        {(student.status || []).map(
                          (status: string, index: number) => (
                            <td
                              key={`${student.nim ?? student.name}-${index}`}
                              className="py-2 text-center"
                            >
                              <span
                                className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-semibold text-white ${
                                  status === "good"
                                    ? "bg-emerald-500"
                                    : status === "mid"
                                      ? "bg-amber-500"
                                      : status === "low"
                                        ? "bg-rose-500"
                                        : "bg-slate-300"
                                }`}
                                title={
                                  status === "none"
                                    ? "Belum mengumpulkan"
                                    : status === "good"
                                      ? "≥ 75"
                                      : status === "mid"
                                        ? "60–74"
                                        : "< 60"
                                }
                              >
                                {status === "good"
                                  ? "A"
                                  : status === "mid"
                                    ? "B"
                                    : status === "low"
                                      ? "D"
                                      : "—"}
                              </span>
                            </td>
                          )
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Per-student scores table */}
      {perStudent.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Nilai Per Mahasiswa</CardTitle>
            <CardDescription>
              Ringkasan nilai rata-rata setiap peserta berdasarkan submission yang sudah dinilai.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 text-xs uppercase tracking-wide border-b border-slate-100">
                    <th className="pb-2 pr-4">NIM</th>
                    <th className="pb-2 pr-4">Nama</th>
                    <th className="pb-2 pr-4 text-right">Avg Score</th>
                    <th className="pb-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {perStudent.map((s) => (
                    <tr key={s.nim} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2 pr-4 font-mono text-xs text-slate-400">{s.nim}</td>
                      <td className="py-2 pr-4 font-medium text-slate-800">{s.name}</td>
                      <td className="py-2 pr-4 text-right">
                        <span
                          className={`font-semibold tabular-nums ${
                            s.avg_score >= 75
                              ? "text-emerald-600"
                              : s.avg_score >= 60
                                ? "text-amber-600"
                                : "text-rose-600"
                          }`}
                        >
                          {s.avg_score.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-2 text-right">
                        <Badge variant={s.status === "pass" ? "success" : "danger"}>
                          {s.status === "pass" ? "Lulus" : "Remedial"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
