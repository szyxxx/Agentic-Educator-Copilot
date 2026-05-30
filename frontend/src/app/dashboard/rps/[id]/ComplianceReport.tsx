"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Criterion = {
  id: string;
  title: string;
  regulation_ref: string;
  severity: "critical" | "warning" | "info";
  scope: "rps_level" | "per_week";
  weight: number;
  contributed_weight: number;
  passed: boolean;
  detail: string;
  field: string;
  group: string;
  target_week: number | null;
  suggested_value: any;
};

type Group = {
  group: string;
  passed: number;
  total: number;
  earned_weight: number;
  total_weight: number;
};

type Report = {
  score: number;
  total_weight: number;
  earned_weight: number;
  regulation_summary: string;
  criteria: Criterion[];
  groups: Group[];
};

const SECTION_ORDER = [
  "Identitas",
  "Capaian Pembelajaran",
  "Bahan Kajian",
  "Pertemuan",
  "Metode & Evaluasi",
  "Referensi",
];

const SECTION_FILL: Record<string, string> = {
  Identitas: "bg-slate-500",
  "Capaian Pembelajaran": "bg-teal-500",
  "Bahan Kajian": "bg-indigo-500",
  Pertemuan: "bg-amber-500",
  "Metode & Evaluasi": "bg-emerald-500",
  Referensi: "bg-rose-500",
};

export default function ComplianceReport({ rpsId }: { rpsId: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string>("");
  const [showAll, setShowAll] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    apiFetch<Report>(`/api/rps/${rpsId}/compliance`)
      .then((data) => {
        setReport(data);
        // Auto-expand sections with failed criteria
        const next: Record<string, boolean> = {};
        for (const g of data.groups) {
          if (g.passed < g.total) next[g.group] = true;
        }
        setExpanded(next);
      })
      .catch((e) => setError(String(e?.message ?? e)));
  }, [rpsId]);

  if (error) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-rose-600">
          Gagal memuat laporan compliance: {error}
        </CardContent>
      </Card>
    );
  }
  if (!report) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-slate-500">
          Memuat laporan SN-DIKTI…
        </CardContent>
      </Card>
    );
  }

  const orderedGroups = [...report.groups].sort(
    (a, b) =>
      SECTION_ORDER.indexOf(a.group) - SECTION_ORDER.indexOf(b.group)
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <CardTitle>Laporan Compliance SN-DIKTI</CardTitle>
            <CardDescription title={report.regulation_summary}>
              Skor terhitung dari {report.criteria.length} kriteria yang dideklarasikan di catalog.
              Hover untuk melihat regulasi yang dirujuk.
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-4xl font-semibold text-slate-800">
              {report.score}%
            </div>
            <div className="text-xs text-slate-500">
              {report.earned_weight} / {report.total_weight} bobot
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <SegmentedBar groups={orderedGroups} totalWeight={report.total_weight} />

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => setShowAll((v) => !v)}
            className="text-[11px] text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
          >
            {showAll ? "Sembunyikan kriteria yang lulus" : "Lihat semua kriteria"}
          </button>
        </div>

        <div className="space-y-2">
          {orderedGroups.map((group) => {
            const groupRows = report.criteria.filter(
              (c) => c.group === group.group
            );
            const visibleRows = showAll
              ? groupRows
              : groupRows.filter((c) => !c.passed);
            if (visibleRows.length === 0) {
              return (
                <div
                  key={group.group}
                  className="rounded-lg border border-emerald-100 bg-emerald-50/40 px-4 py-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2 text-sm text-emerald-800">
                    <span>✓</span>
                    <span className="font-medium">{group.group}</span>
                    <span className="text-xs text-emerald-600">
                      semua {group.total} kriteria lulus
                    </span>
                  </div>
                  <div className="text-xs text-emerald-700">
                    +{group.earned_weight}
                  </div>
                </div>
              );
            }
            const isOpen = expanded[group.group] ?? true;
            return (
              <div
                key={group.group}
                className="rounded-lg border border-slate-200 bg-white"
              >
                <button
                  type="button"
                  onClick={() =>
                    setExpanded((prev) => ({
                      ...prev,
                      [group.group]: !isOpen,
                    }))
                  }
                  className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-sm">
                      {isOpen ? "▾" : "▸"}
                    </span>
                    <span className="font-medium text-slate-800">
                      {group.group}
                    </span>
                    <span className="text-xs text-slate-500">
                      {group.passed}/{group.total} kriteria lulus
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">
                    {group.earned_weight} / {group.total_weight} bobot
                  </span>
                </button>
                {isOpen && (
                  <ul className="divide-y divide-slate-100 px-4 pb-3">
                    {visibleRows.map((row, idx) => (
                      <li
                        key={`${row.id}-${row.target_week ?? "x"}-${idx}`}
                        className="py-3 flex flex-col gap-1"
                      >
                        <div className="flex items-start gap-2">
                          <span
                            className={`text-base leading-none mt-0.5 ${
                              row.passed
                                ? "text-emerald-500"
                                : "text-rose-500"
                            }`}
                          >
                            {row.passed ? "✓" : "✗"}
                          </span>
                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-sm font-medium text-slate-800">
                                {row.title}
                              </span>
                              <Badge
                                variant="outline"
                                className="text-[10px] px-1.5 py-0"
                                title={row.regulation_ref}
                              >
                                {row.regulation_ref.split(",")[0]}
                              </Badge>
                              {row.target_week && (
                                <a
                                  href={`#modul-${row.target_week}`}
                                  className="text-[11px] text-teal-600 hover:underline"
                                >
                                  Modul {row.target_week}
                                </a>
                              )}
                              <span
                                className={`ml-auto text-xs font-mono ${
                                  row.passed
                                    ? "text-emerald-600"
                                    : "text-slate-400 line-through"
                                }`}
                              >
                                {row.passed ? "+" : ""}
                                {row.weight}
                              </span>
                            </div>
                            {row.detail && (
                              <p className="mt-0.5 text-xs text-slate-500">
                                {row.detail}
                              </p>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function SegmentedBar({
  groups,
  totalWeight,
}: {
  groups: Group[];
  totalWeight: number;
}) {
  if (totalWeight === 0) return null;
  return (
    <div className="space-y-1.5">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
        {groups.map((g) => {
          const widthPct = (g.total_weight / totalWeight) * 100;
          const fillPct =
            g.total_weight === 0
              ? 0
              : (g.earned_weight / g.total_weight) * 100;
          const baseColor = SECTION_FILL[g.group] ?? "bg-slate-400";
          return (
            <div
              key={g.group}
              className="h-full relative"
              style={{ width: `${widthPct}%` }}
              title={`${g.group}: ${g.earned_weight}/${g.total_weight}`}
            >
              <div
                className={`absolute left-0 top-0 bottom-0 ${baseColor}`}
                style={{ width: `${fillPct}%` }}
              />
              <div className="absolute inset-0 border-r border-white/70" />
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500">
        {groups.map((g) => (
          <div key={g.group} className="flex items-center gap-1">
            <span
              className={`h-2 w-2 rounded-full ${
                SECTION_FILL[g.group] ?? "bg-slate-400"
              }`}
            />
            <span>
              {g.group}: {g.passed}/{g.total}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
