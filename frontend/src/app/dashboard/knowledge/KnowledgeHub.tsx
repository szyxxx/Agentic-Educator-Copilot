"use client";

import { useState } from "react";

import { KnowledgeView } from "./KnowledgeView";
import { KnowledgeNetwork } from "./KnowledgeNetwork";
import { RagSearch } from "./RagSearch";

type Course = { id: string; name: string; code: string };

type Props = {
  data: any;
  courses: Course[];
};

type Tab = "materials" | "network" | "rag";

export function KnowledgeHub({ data, courses }: Props) {
  const [tab, setTab] = useState<Tab>("materials");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">🧠 Knowledge Hub</h1>
        <p className="mt-1 text-sm text-slate-500">
          Pusat referensi dan materi yang dipakai AI untuk menyusun RPS, kuis, dan jawaban kontekstual.
          Termasuk visualisasi knowledge network dan pencarian semantik (RAG).
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-200">
        <TabBtn active={tab === "materials"} onClick={() => setTab("materials")}>
          📁 Materi & Referensi
        </TabBtn>
        <TabBtn active={tab === "network"} onClick={() => setTab("network")}>
          🕸️ Knowledge Network
        </TabBtn>
        <TabBtn active={tab === "rag"} onClick={() => setTab("rag")}>
          🔎 RAG Search
        </TabBtn>
      </div>

      {tab === "materials" && <KnowledgeView data={data} courses={courses} />}
      {tab === "network" && <KnowledgeNetwork />}
      {tab === "rag" && <RagSearch />}
    </div>
  );
}

function TabBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
        active
          ? "border-teal-600 text-teal-700"
          : "border-transparent text-slate-500 hover:text-slate-700"
      }`}
    >
      {children}
    </button>
  );
}
