import Link from "next/link";
import { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Beranda", icon: "📊" },
  { href: "/dashboard/courses", label: "Mata Kuliah", icon: "📚" },
  { href: "/dashboard/rps", label: "Rencana Pembelajaran (RPS)", icon: "🗒️" },
  { href: "/dashboard/quiz", label: "Kuis & Evaluasi", icon: "📝" },
  { href: "/dashboard/analytics", label: "Analitik Kelas", icon: "📈" },
  { href: "/dashboard/knowledge", label: "Knowledge Hub", icon: "🧠" },
  { href: "/dashboard/settings", label: "Pengaturan", icon: "⚙️" },
];

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  let activeClassesCount = 0;
  try {
    const data = await apiFetch<any>("/api/dashboard/overview");
    if (data && data.stats_blocks) {
      const activeBlock = data.stats_blocks.find(
        (b: any) => b.label === "Mata Kuliah Aktif"
      );
      if (activeBlock) {
        activeClassesCount = parseInt(activeBlock.value) || 0;
      }
    }
  } catch (error) {
    console.error("Failed to fetch overview data for layout", error);
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-[1400px] gap-6 px-6 py-6">
        <aside className="w-72 shrink-0">
          <div className="sticky top-6 flex h-[calc(100vh-3rem)] flex-col rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm shadow-slate-900/10 backdrop-blur overflow-y-auto">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                  EduCopilot
                </p>
                <h1 className="text-2xl font-semibold text-slate-900">
                  Educator Suite
                </h1>
              </div>
              <Badge variant="outline">2025/26</Badge>
            </div>

            <nav className="mt-6 flex-1 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-2xl px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-900 hover:text-white"
                >
                  <span className="text-base">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="mt-auto pt-6">
              <div className="rounded-2xl border border-slate-200/70 bg-slate-50 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                  Status Semester
                </p>
                <p className="mt-2 text-sm text-slate-700">
                  {activeClassesCount > 0
                    ? `${activeClassesCount} mata kuliah sedang aktif berjalan.`
                    : "Belum ada mata kuliah aktif semester ini."}
                </p>
                <Link href="/dashboard/analytics" className="mt-4 block">
                  <Button className="w-full" size="sm" variant="secondary">
                    Lihat Analitik Kelas
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex-1 space-y-6">
          <header className="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm shadow-slate-900/10 backdrop-blur">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">
                  EduCopilot — Asisten Kurikulum AI
                </p>
                <h2 className="text-2xl font-semibold text-slate-900">
                  Ruang Kerja Dosen
                </h2>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link href="/dashboard/rps/new">
                  <Button variant="secondary">+ Buat RPS</Button>
                </Link>
                <Link href="/dashboard/quiz/new">
                  <Button variant="outline">+ Buat Kuis</Button>
                </Link>
              </div>
            </div>
          </header>

          <main className="space-y-6">{children}</main>
        </div>
      </div>
    </div>
  );
}