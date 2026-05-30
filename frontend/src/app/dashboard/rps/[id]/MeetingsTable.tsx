"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import WeekFeedback from "./WeekFeedback";
import WeekMaterials from "./WeekMaterials";

type Meeting = {
  week: string;
  week_number: number;
  is_exam_week: boolean;
  bahan_kajian_topik: string;
  sub_topic_title: string;
  sub_topic_description: string;
  cpmk_number: number | null;
  reference_indices: number[];
  topic?: string;
  cpmk?: string;
  references?: string;
  method?: string;
  evaluation?: string;
  feedback?: string;
  status: string;
  status_text: string;
};

type Props = {
  rpsId: string;
  courseId: string;
  meetings: Meeting[];
  referencesList: string[];
  cpmkList: string[];
  rpsStatus: string;
};

/**
 * Institutional 5-column meetings table with optional disclosure for the
 * internal pedagogy columns (Metode, Evaluasi, Materi, Feedback, Status).
 */
export default function MeetingsTable({
  rpsId,
  courseId,
  meetings,
  referencesList,
  cpmkList,
  rpsStatus,
}: Props) {
  const [internalOpen, setInternalOpen] = useState(false);

  const refTooltip = (indices: number[]) =>
    indices
      .map((idx) => `${idx}. ${referencesList[idx - 1] ?? "(referensi hilang)"}`)
      .join("\n");

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => setInternalOpen((v) => !v)}
          className="text-[11px] text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
        >
          {internalOpen ? "▾ Sembunyikan" : "▸ Tampilkan"} kolom internal
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="pb-2 pr-3 font-semibold">Modul</th>
              <th className="pb-2 pr-3 font-semibold">Bahan Kajian/Topik</th>
              <th className="pb-2 pr-3 font-semibold">Sub-Topik</th>
              <th className="pb-2 pr-3 font-semibold whitespace-nowrap">
                CPMK Terkait
              </th>
              <th className="pb-2 pr-3 font-semibold whitespace-nowrap">
                No. Referensi
              </th>
              {internalOpen && (
                <>
                  <th className="pb-2 pr-3 font-semibold">Metode</th>
                  <th className="pb-2 pr-3 font-semibold">Evaluasi</th>
                  <th className="pb-2 pr-3 font-semibold">Materi</th>
                  <th className="pb-2 pr-3 font-semibold">Feedback</th>
                  <th className="pb-2 font-semibold">Status</th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {meetings.map((meeting) => {
              const week = meeting.week_number;
              const exam = meeting.is_exam_week;
              return (
                <tr key={week} className={exam ? "bg-rose-50/40" : ""}>
                  <td className="py-2 pr-3 font-medium text-slate-700 align-top">
                    {week}
                  </td>
                  <td className="py-2 pr-3 align-top italic text-slate-600">
                    {exam ? (
                      <span className="text-rose-500">—</span>
                    ) : (
                      meeting.bahan_kajian_topik || (
                        <span className="text-slate-400 not-italic">—</span>
                      )
                    )}
                  </td>
                  <td className="py-2 pr-3 align-top text-slate-700">
                    {exam ? (
                      <span className="italic">{meeting.sub_topic_title}</span>
                    ) : (
                      <>
                        <span className="font-semibold">
                          {meeting.sub_topic_title}
                        </span>
                        {meeting.sub_topic_description && (
                          <>
                            <span>: </span>
                            <span className="font-normal text-slate-600">
                              {meeting.sub_topic_description}
                            </span>
                          </>
                        )}
                      </>
                    )}
                  </td>
                  <td className="py-2 pr-3 align-top text-center text-slate-600">
                    {exam ? (
                      "—"
                    ) : meeting.cpmk_number !== null && meeting.cpmk_number !== undefined ? (
                      <span
                        title={`CPMK-${meeting.cpmk_number}: ${
                          cpmkList[meeting.cpmk_number - 1] ?? ""
                        }`}
                      >
                        {meeting.cpmk_number}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td
                    className="py-2 pr-3 align-top text-center text-slate-600"
                    title={
                      meeting.reference_indices?.length
                        ? refTooltip(meeting.reference_indices)
                        : undefined
                    }
                  >
                    {exam
                      ? "—"
                      : meeting.reference_indices?.length
                        ? meeting.reference_indices.join(", ")
                        : "—"}
                  </td>
                  {internalOpen && (
                    <>
                      <td className="py-2 pr-3 text-slate-600 align-top">
                        {meeting.method || "—"}
                      </td>
                      <td className="py-2 pr-3 text-slate-600 align-top">
                        {meeting.evaluation || "—"}
                      </td>
                      <td className="py-2 pr-3 align-top w-[210px]">
                        <WeekMaterials
                          rpsId={rpsId}
                          courseId={courseId}
                          weekNumber={week}
                          cpmk={
                            meeting.cpmk_number
                              ? `CPMK-${meeting.cpmk_number}`
                              : ""
                          }
                        />
                      </td>
                      <td className="py-2 pr-3 align-top">
                        <WeekFeedback
                          rpsId={rpsId}
                          weekNumber={week}
                          initialFeedback={meeting.feedback || ""}
                          status={rpsStatus}
                        />
                      </td>
                      <td className="py-2 align-top">
                        <Badge
                          variant={
                            meeting.status === "ok"
                              ? "success"
                              : meeting.status === "warning"
                                ? "warning"
                                : "danger"
                          }
                        >
                          {meeting.status_text}
                        </Badge>
                      </td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
