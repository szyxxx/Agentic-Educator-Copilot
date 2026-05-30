"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import RpsForm, { RpsFormData, blankRps } from "../rps-form";
import { apiFetch } from "@/lib/api";

function NewRPSContent() {
  const search = useSearchParams();
  const courseId = search.get("course_id");
  const [data, setData] = useState<RpsFormData>(blankRps());
  const [ready, setReady] = useState(!courseId);

  useEffect(() => {
    if (!courseId) return;
    apiFetch<any[]>("/api/courses/")
      .then((courses) => {
        const c = courses.find((x) => x.id === courseId);
        if (c) {
          setData((prev) => ({
            ...prev,
            course_name: c.name,
            course_code: c.code,
            sks: c.sks,
            semester: c.semester,
            program_study: c.program_study,
          }));
        }
      })
      .finally(() => setReady(true));
  }, [courseId]);

  if (!ready) return <div className="p-8">Memuat data mata kuliah...</div>;
  return <RpsForm mode="new" initialData={data} />;
}

export default function NewRPSPage() {
  return (
    <Suspense fallback={<div className="p-8">Memuat...</div>}>
      <NewRPSContent />
    </Suspense>
  );
}
