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
import { apiFetch, apiUrl } from "@/lib/api";

async function deleteRPS(formData: FormData) {
  "use server";
  const id = formData.get("id") as string;
  await fetch(apiUrl(`/api/rps/${id}`), { method: "DELETE" });
  revalidatePath("/dashboard/rps");
}

export default async function RPSManagement() {
  const data = await apiFetch<any>("/api/dashboard/rps");

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">🗒️ Rencana Pembelajaran Semester</h1>
          <p className="mt-1 text-sm text-slate-500">
            Buat, edit, dan kelola dokumen RPS tiap mata kuliah.
          </p>
        </div>
        <Link href="/dashboard/rps/new">
          <Button>✨ Buat RPS Baru</Button>
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

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Daftar RPS</h2>
          <span className="text-sm text-slate-500">
            {data.items.length} dokumen
          </span>
        </div>

        {data.items.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-slate-500">
              Belum ada RPS. Klik "Buat RPS Baru" untuk membuat secara manual atau dengan AI.
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          {data.items.map((rps: any) => (
            <Card key={rps.id}>
              <CardHeader>
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle className="text-xl">{rps.course}</CardTitle>
                    <CardDescription>{rps.details}</CardDescription>
                  </div>
                  <Badge
                    variant={rps.status === "compliant" ? "success" : "warning"}
                  >
                    {rps.status_text}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-xs text-slate-500">
                      Skor Kesesuaian SN-Dikti
                    </p>
                    <p className="text-2xl font-semibold text-slate-900">
                      {rps.compliance_score}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Isu Belum Diperbaiki</p>
                    <p className="text-2xl font-semibold text-slate-900">
                      {rps.issues_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Terakhir Diperbarui</p>
                    <p className="text-sm font-medium text-slate-700">
                      {rps.updated_at}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <Link href={`/dashboard/rps/${rps.id}`}>
                    <Button size="sm" variant="secondary">
                      Lihat Detail
                    </Button>
                  </Link>
                  <Link href={`/dashboard/rps/${rps.id}/edit`}>
                    <Button size="sm" variant="outline">
                      Edit
                    </Button>
                  </Link>
                  <form action={deleteRPS} className="ml-auto">
                    <input type="hidden" name="id" value={rps.id} />
                    <Button type="submit" size="sm" variant="danger">
                      Hapus
                    </Button>
                  </form>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
