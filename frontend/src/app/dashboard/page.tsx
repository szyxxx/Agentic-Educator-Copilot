import Link from "next/link";
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
import { apiFetch } from "@/lib/api";

export default async function DashboardOverview() {
  const data = await apiFetch<any>("/api/dashboard/overview");

  return (
    <div className="space-y-6">
      <Card className="border-none bg-gradient-to-br from-slate-900 via-slate-900 to-teal-700 text-white">
        <CardContent className="p-8">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-3">
              <Badge variant="outline" className="border-white/40 text-white/80">
                ✨ EduCopilot AI Aktif
              </Badge>
              <h1 className="text-3xl font-semibold">
                {data.educator.name
                  ? `Selamat datang, ${data.educator.name} 👋`
                  : "Selamat datang di EduCopilot"}
              </h1>
              <p className="text-white/70">
                {data.educator.semester || "Atur semester aktif di Pengaturan"}
              </p>
              <p className="max-w-xl text-sm text-white/70">
                Gunakan EduCopilot untuk menyusun RPS yang sesuai SN-Dikti, membuat kuis otomatis, dan memantau progres belajar mahasiswa — semuanya di satu tempat.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <Link href="/dashboard/rps/new" className="w-full">
                <Button variant="outline" className="w-full border-transparent bg-white text-slate-900 hover:bg-slate-100 hover:text-slate-900">
                  ✨ Buat RPS dengan AI
                </Button>
              </Link>
              <Link href="/dashboard/quiz/new" className="w-full">
                <Button variant="outline" className="w-full border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white">
                  📝 Buat Kuis Baru
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {data.stats_blocks.map((stat: any) => (
          <Card key={stat.label}>
            <CardHeader className="pb-2">
              <CardDescription>{stat.label}</CardDescription>
              <CardTitle className="text-3xl">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-slate-500">{stat.note}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Rata-rata Nilai per Mata Kuliah</CardTitle>
            <CardDescription>
              Tren nilai mingguan dari kuis yang sudah dikumpulkan.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {data.course_pulse.length === 0 && (
              <p className="text-sm text-slate-500">
                Belum ada data nilai. Tren akan muncul setelah ada submission yang dinilai.
              </p>
            )}
            {data.course_pulse.map((course: any) => (
              <div key={course.course} className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-700">
                    {course.course}
                  </p>
                  <span className="text-sm text-slate-500">
                    Avg {course.avg}
                  </span>
                </div>
                <div className="flex h-16 items-end gap-1">
                  {course.trend.map((value: number, index: number) => (
                    <div
                      key={`${course.course}-${index}`}
                      className="w-5 rounded-full bg-teal-500/60"
                      style={{ height: `${value}%` }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Perlu Ditindaklanjuti</CardTitle>
            <CardDescription>Item yang memerlukan aksi dosen secepatnya.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.alerts.map((alert: any) => (
              <div
                key={alert.id}
                className="rounded-2xl border border-slate-200/70 bg-slate-50 p-4"
              >
                <p className="text-sm font-medium text-slate-800">
                  {alert.title}
                </p>
                <p className="mt-1 text-xs text-slate-500">{alert.note}</p>
                <div className="mt-3">
                  <Link href="/dashboard/rps">
                    <Button size="sm" variant="outline">
                      Tindak Lanjut
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Aktivitas Terbaru</CardTitle>
            <CardDescription>Log aktivitas terakhir di sistem — pembuatan RPS, kuis, dan respons AI.</CardDescription>
          </CardHeader>
          <CardContent>
            {data.recent_activities.length === 0 ? (
              <p className="text-sm text-slate-500">
                Belum ada aktivitas tercatat.
              </p>
            ) : (
              <ul className="space-y-3">
                {data.recent_activities.map((act: any) => (
                  <li key={act.id} className="flex items-center gap-3 text-sm">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        act.type === "info"
                          ? "bg-sky-500"
                          : act.type === "success"
                            ? "bg-emerald-500"
                            : "bg-amber-500"
                      }`}
                    />
                    <span className="text-slate-600">{act.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Jadwal Kuis Mendatang</CardTitle>
            <CardDescription>Kuis aktif dan tenggat pengumpulan terdekat.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.calendar.length === 0 ? (
              <p className="text-sm text-slate-500">
                Tidak ada kuis aktif saat ini.
              </p>
            ) : (
              data.calendar.map((item: any) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-2xl border border-slate-200/70 bg-white px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {item.title}
                    </p>
                    <p className="text-xs text-slate-500">{item.course}</p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <p>{item.date}</p>
                    <p>{item.time}</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Checklist Penyelesaian Semester</CardTitle>
          <CardDescription>
            Progres penyelesaian tugas-tugas administratif dan pedagogi dosen.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.focus_actions.map((action: any) => (
            <div key={action.label} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">
                  {action.label}
                </span>
                <span className="text-slate-500">{action.value}%</span>
              </div>
              <Progress value={action.value} colorClassName={action.color} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
