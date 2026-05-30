"use client";

import { useEffect, useState, use } from "react";

import RpsForm, { RpsFormData, blankRps } from "../../rps-form";
import { apiFetch } from "@/lib/api";

const cleanItem = (c: string) => {
  let cleaned = c.trim();

  // Strip raw JSON dumps like '{"cpl": ["..."]}' that the old buggy AI fallback
  // could leak into cpl_list. Try to recover the inner string when possible.
  if (cleaned.startsWith("{")) {
    try {
      const parsed = JSON.parse(cleaned);
      if (Array.isArray(parsed?.cpl) && parsed.cpl.length) {
        cleaned = String(parsed.cpl[0]);
      } else if (Array.isArray(parsed?.cpmk) && parsed.cpmk.length) {
        cleaned = String(parsed.cpmk[0]);
      }
    } catch {
      // not valid JSON, fall through
    }
  }

  return cleaned
    .replace(/^\**CPL-\d+:\**\s*/i, "")
    .replace(/^\**CPMK-\d+:\**\s*/i, "")
    .replace(/\**/g, "")
    .replace(/^\d+\.\s*/, "")
    .trim();
};

const sanitize = (list: string[] | undefined): string[] => {
  if (!list || list.length === 0) return [""];
  return list
    .map(cleanItem)
    .filter((c) => c && !c.toLowerCase().includes("capaian pembelajaran"));
};

export default function EditRPSPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolved = use(params);
  const rpsId = resolved.id;
  const [data, setData] = useState<RpsFormData | null>(null);
  const [courseLabel, setCourseLabel] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    apiFetch<any>(`/api/dashboard/rps/${rpsId}`)
      .then((d) => {
        const meetings = (d.meetings || []).map((m: any) => {
          const week =
            typeof m.week === "string"
              ? parseInt(String(m.week).replace("W", "")) || 0
              : (m.week_number ?? m.week ?? 0);
          return {
            week,
            bahan_kajian_topik: m.bahan_kajian_topik || "",
            sub_topic_title: m.sub_topic_title || m.topic || "",
            sub_topic_description: m.sub_topic_description || "",
            cpmk_number:
              typeof m.cpmk_number === "number" ? m.cpmk_number : null,
            reference_indices: Array.isArray(m.reference_indices)
              ? m.reference_indices
              : [],
            method: m.method || "",
            evaluation: m.evaluation || "",
          };
        });
        // Pad up to 16 weeks if backend returned fewer
        while (meetings.length < 16) {
          const week = meetings.length + 1;
          const examTitle =
            week === 8
              ? "Ujian Tengah Semester (UTS)"
              : week === 16
                ? "Ujian Akhir Semester (UAS)"
                : "";
          meetings.push({
            week,
            bahan_kajian_topik: "",
            sub_topic_title: examTitle,
            sub_topic_description: "",
            cpmk_number: null,
            reference_indices: [],
            method: "",
            evaluation: "",
          });
        }
        const baseline = blankRps();
        setData({
          ...baseline,
          cpl_list: sanitize(d.cpl_list),
          cpmk_list: sanitize(d.cpmk_list),
          references_list:
            d.references_list && d.references_list.length > 0
              ? d.references_list
              : [""],
          bahan_kajian:
            d.bahan_kajian && d.bahan_kajian.length > 0
              ? d.bahan_kajian
              : [""],
          learning_methods: Array.isArray(d.learning_methods)
            ? d.learning_methods
            : [],
          learning_modality: d.learning_modality || "",
          meetings,
        });
        setCourseLabel(d.course || "");
      })
      .catch((e) => setError(e.message));
  }, [rpsId]);

  if (error) {
    return <div className="p-8 text-red-600">Gagal memuat: {error}</div>;
  }
  if (!data) return <div className="p-8">Memuat data RPS...</div>;

  return (
    <RpsForm
      mode="edit"
      rpsId={rpsId}
      initialData={data}
      courseLabel={courseLabel}
    />
  );
}
