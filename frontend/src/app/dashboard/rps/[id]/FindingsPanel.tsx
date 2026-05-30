"use client";

import { useEffect, useState } from "react";
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

type Finding = {
  id: string;
  rps_id: string;
  severity: "critical" | "warning" | "info";
  scope: "per_week" | "cross_cutting";
  target_week: number | null;
  category:
    | "sndikti_compliance"
    | "cpmk_alignment"
    | "cpl_alignment"
    | "content_quality"
    | "continuity";
  field: string | null;
  issue: string;
  suggested_fix: string | null;
  suggested_value: any;
  regulation_ref: string | null;
  criterion_id: string | null;
  dismissed: boolean;
  applied: boolean;
  last_seen_at: string | null;
};

type FindingsResponse = {
  findings: Finding[];
  summary_counts: {
    severity: { critical: number; warning: number; info: number };
    category: Record<string, number>;
  };
  last_reviewed_at: string | null;
};

const CATEGORY_ORDER: Finding["category"][] = [
  "sndikti_compliance",
  "cpmk_alignment",
  "cpl_alignment",
  "content_quality",
  "continuity",
];

const CATEGORY_LABELS: Record<Finding["category"], string> = {
  sndikti_compliance: "Compliance SN-DIKTI",
  cpmk_alignment: "Keselarasan CPMK",
  cpl_alignment: "Keselarasan CPL",
  content_quality: "Kualitas Konten",
  continuity: "Kesinambungan Antar Minggu",
};

const SEVERITY_BADGE: Record<Finding["severity"], "danger" | "warning" | "outline"> = {
  critical: "danger",
  warning: "warning",
  info: "outline",
};

export default function FindingsPanel({ rpsId }: { rpsId: string }) {
  const router = useRouter();
  const [data, setData] = useState<FindingsResponse | null>(null);
  const [showDismissed, setShowDismissed] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string>("");
  const [busyId, setBusyId] = useState<string>("");

  const load = async (includeDismissed: boolean = showDismissed) => {
    try {
      const res = await apiFetch<FindingsResponse>(
        `/api/rps/${rpsId}/findings?include_dismissed=${includeDismissed}`
      );
      setData(res);
    } catch (e: any) {
      setError(String(e?.message ?? e));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rpsId]);

  const runReview = async () => {
    setRunning(true);
    setError("");
    try {
      await apiFetch(`/api/rps/${rpsId}/review`, { method: "POST" });
      await load();
      router.refresh();
    } catch (e: any) {
      setError(String(e?.message ?? e));
    } finally {
      setRunning(false);
    }
  };

  const apply = async (id: string) => {
    setBusyId(id);
    try {
      await apiFetch(`/api/rps/${rpsId}/findings/${id}/apply`, {
        method: "POST",
      });
      await load();
      router.refresh();
    } catch (e: any) {
      alert(`Gagal terapkan: ${e.message}`);
    } finally {
      setBusyId("");
    }
  };

  const dismiss = async (id: string) => {
    setBusyId(id);
    try {
      await apiFetch(`/api/rps/${rpsId}/findings/${id}/dismiss`, {
        method: "POST",
      });
      await load();
    } catch (e: any) {
      alert(`Gagal tutup: ${e.message}`);
    } finally {
      setBusyId("");
    }
  };

  const reopen = async (id: string) => {
    setBusyId(id);
    try {
      await apiFetch(`/api/rps/${rpsId}/findings/${id}/reopen`, {
        method: "POST",
      });
      await load();
    } catch (e: any) {
      alert(`Gagal buka kembali: ${e.message}`);
    } finally {
      setBusyId("");
    }
  };

  const toggleDismissed = async () => {
    const next = !showDismissed;
    setShowDismissed(next);
    await load(next);
  };

  const findings = data?.findings ?? [];
  const activeFindings = findings.filter((f) => !f.dismissed);
  const dismissedFindings = findings.filter((f) => f.dismissed);

  const lastReviewed = data?.last_reviewed_at;
  const counts = data?.summary_counts?.severity ?? {
    critical: 0,
    warning: 0,
    info: 0,
  };

  // First-run hero state
  if (!lastReviewed && activeFindings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Agent Review RPS</CardTitle>
          <CardDescription>
            Jalankan agent untuk menganalisis kualitas RPS, kesesuaian SN-DIKTI, kesinambungan minggu, dan keselarasan CPMK. Tidak ada perubahan yang ditulis ke RPS — hanya temuan yang bisa Anda terapkan satu per satu.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center text-center py-10 gap-3">
          <p className="text-sm text-slate-500 max-w-md">
            Jalankan review otomatis untuk RPS ini untuk melihat field mana yang lemah dan rekomendasi spesifik per pertemuan.
          </p>
          <Button
            onClick={runReview}
            disabled={running}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {running ? "Menjalankan review…" : "🔍 Jalankan Review"}
          </Button>
          {error && (
            <p className="text-xs text-rose-600">{error}</p>
          )}
        </CardContent>
      </Card>
    );
  }

  // No active findings (positive state)
  if (activeFindings.length === 0 && !showDismissed) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle>Agent Review RPS</CardTitle>
              <CardDescription>
                Tidak ada temuan saat ini. RPS dianggap memadai.
              </CardDescription>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Button
                size="sm"
                onClick={runReview}
                disabled={running}
                variant="outline"
              >
                {running ? "…" : "🔄 Jalankan Ulang"}
              </Button>
              {dismissedFindings.length > 0 && (
                <button
                  type="button"
                  onClick={toggleDismissed}
                  className="text-[11px] text-slate-500 hover:underline"
                >
                  Tampilkan {dismissedFindings.length} yang sudah ditutup
                </button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-emerald-600 text-sm">
            ✓ Tidak ada temuan aktif.{" "}
            {lastReviewed && (
              <span className="text-slate-500">
                Terakhir di-review {new Date(lastReviewed).toLocaleString("id-ID")}.
              </span>
            )}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <CardTitle>Temuan Review</CardTitle>
            <CardDescription>
              {lastReviewed && (
                <>
                  Terakhir di-review:{" "}
                  {new Date(lastReviewed).toLocaleString("id-ID")}.{" "}
                </>
              )}
              Klik "Terapkan Saran" untuk menambal field yang ditunjuk; klik "Tutup" untuk mengabaikan.
            </CardDescription>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex gap-1.5">
              {counts.critical > 0 && (
                <Badge variant="danger">{counts.critical} kritis</Badge>
              )}
              {counts.warning > 0 && (
                <Badge variant="warning">{counts.warning} peringatan</Badge>
              )}
              {counts.info > 0 && (
                <Badge variant="outline">{counts.info} info</Badge>
              )}
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={runReview}
              disabled={running}
            >
              {running ? "Menjalankan…" : "🔄 Jalankan Ulang"}
            </Button>
            <button
              type="button"
              onClick={toggleDismissed}
              className="text-[11px] text-slate-500 hover:underline"
            >
              {showDismissed
                ? "Sembunyikan yang sudah ditutup"
                : `Tampilkan ${dismissedFindings.length} yang sudah ditutup`}
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {error && (
          <p className="text-xs text-rose-600">{error}</p>
        )}
        {CATEGORY_ORDER.map((cat) => {
          const rows = (
            showDismissed ? findings : activeFindings
          ).filter((f) => f.category === cat);
          if (rows.length === 0) return null;
          return (
            <div key={cat} className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {CATEGORY_LABELS[cat]} <span className="text-slate-400">({rows.length})</span>
              </h3>
              <ul className="space-y-2">
                {rows.map((f) => (
                  <li
                    key={f.id}
                    className={`rounded-lg border p-3 ${
                      f.dismissed
                        ? "bg-slate-50/60 border-slate-200 opacity-70"
                        : f.severity === "critical"
                          ? "border-rose-200 bg-rose-50/40"
                          : f.severity === "warning"
                            ? "border-amber-200 bg-amber-50/40"
                            : "border-slate-200 bg-white"
                    }`}
                  >
                    <div className="flex flex-wrap items-start gap-2">
                      <Badge variant={SEVERITY_BADGE[f.severity]}>
                        {f.severity}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {f.target_week ? `Modul ${f.target_week}` : "RPS"}
                      </Badge>
                      {f.field && (
                        <Badge variant="outline" className="text-[10px]">
                          {f.field}
                        </Badge>
                      )}
                      {f.regulation_ref && (
                        <Badge
                          variant="outline"
                          className="text-[10px]"
                          title={f.regulation_ref}
                        >
                          {f.regulation_ref.split(",")[0]}
                        </Badge>
                      )}
                      <div className="ml-auto flex gap-1.5">
                        {!f.dismissed && f.suggested_value !== null && f.suggested_value !== undefined && !f.applied && (
                          <Button
                            size="sm"
                            onClick={() => apply(f.id)}
                            disabled={busyId === f.id}
                            className="bg-teal-600 hover:bg-teal-700 text-white h-7 text-[11px] px-2"
                          >
                            ✓ Terapkan Saran
                          </Button>
                        )}
                        {f.dismissed ? (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-[11px] px-2"
                            onClick={() => reopen(f.id)}
                            disabled={busyId === f.id}
                          >
                            Buka Kembali
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-[11px] px-2"
                            onClick={() => dismiss(f.id)}
                            disabled={busyId === f.id}
                          >
                            Tutup
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-slate-800">{f.issue}</p>
                    {f.suggested_fix && (
                      <p className="mt-1 text-xs text-slate-500">
                        💡 {f.suggested_fix}
                      </p>
                    )}
                    {f.applied && (
                      <p className="mt-1 text-[11px] text-emerald-600">
                        ✓ Sudah diterapkan ke RPS.
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
