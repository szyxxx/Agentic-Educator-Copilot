"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

type Course = { id: string; name: string; code: string };

type Result = {
  snippet: string;
  title: string;
  type: string;
  course_id: string;
  rps_id?: string;
  week?: number;
};

export function RagSearch() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<Course[]>("/api/courses/").then(setCourses);
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await apiFetch<{ results: Result[] }>(
        "/api/knowledge/query",
        {
          method: "POST",
          json: { query, course_id: courseId || null, k: 5 },
        }
      );
      setResults(data.results);
    } catch (e: any) {
      alert(`Pencarian gagal: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row gap-3">
        <select
          value={courseId}
          onChange={(e) => setCourseId(e.target.value)}
          className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm md:w-64"
        >
          <option value="">Semua Mata Kuliah</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.code} — {c.name}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch();
          }}
          placeholder="Tanya sesuatu, mis. 'apa itu backpropagation'…"
          className="flex-1 h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
        />
        <Button
          onClick={handleSearch}
          disabled={loading}
          className="bg-teal-600 hover:bg-teal-700"
        >
          {loading ? "Mencari…" : "Cari"}
        </Button>
      </div>

      {results == null ? (
        <p className="text-sm text-slate-500">
          Cari materi terindeks. Hasil diambil dari ChromaDB berdasarkan similaritas vektor.
        </p>
      ) : results.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-slate-500">
            Tidak ada hasil. Pastikan ada materi PDF/TXT yang sudah terindeks.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {results.map((r, i) => (
            <Card key={i}>
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{r.type || "MATERIAL"}</Badge>
                  <span className="text-sm font-semibold text-slate-800">
                    {r.title}
                  </span>
                  {r.week ? (
                    <span className="text-xs text-slate-500">
                      • Minggu {r.week}
                    </span>
                  ) : null}
                </div>
                <p className="text-sm text-slate-600 whitespace-pre-wrap">
                  {r.snippet}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
