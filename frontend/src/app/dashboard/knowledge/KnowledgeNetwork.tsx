"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { apiFetch } from "@/lib/api";

type GraphNode = {
  id: string;
  label: string;
  type: "course" | "cpl" | "cpmk" | "week" | "reference" | "material";
  meta?: Record<string, any>;
};

type GraphEdge = {
  source: string;
  target: string;
  kind: string;
};

type Course = { id: string; name: string; code: string };

const TYPE_ORDER: GraphNode["type"][] = [
  "course",
  "cpl",
  "cpmk",
  "week",
  "reference",
  "material",
];

const TYPE_COLOR: Record<GraphNode["type"], string> = {
  course: "#0f172a",
  cpl: "#0d9488",
  cpmk: "#4f46e5",
  week: "#0284c7",
  reference: "#b45309",
  material: "#be123c",
};

const TYPE_LABEL: Record<GraphNode["type"], string> = {
  course: "Mata Kuliah",
  cpl: "CPL",
  cpmk: "CPMK",
  week: "Minggu / Topik",
  reference: "Referensi",
  material: "Materi PDF",
};

type Layout = {
  width: number;
  height: number;
  positions: Record<string, { x: number; y: number }>;
};

function layoutGraph(nodes: GraphNode[]): Layout {
  // Bucket nodes by type, then evenly distribute vertically inside each column.
  const buckets: Record<string, GraphNode[]> = {};
  for (const t of TYPE_ORDER) buckets[t] = [];
  for (const n of nodes) buckets[n.type]?.push(n);

  const COLUMN_GAP = 260;
  const PADDING_Y = 60;
  const MIN_ROW = 36;
  const positions: Record<string, { x: number; y: number }> = {};

  const colHeights = TYPE_ORDER.map(
    (t) => Math.max(buckets[t].length, 1) * MIN_ROW + PADDING_Y * 2
  );
  const height = Math.max(...colHeights, 520);
  const width = TYPE_ORDER.length * COLUMN_GAP + 80;

  TYPE_ORDER.forEach((t, colIdx) => {
    const col = buckets[t];
    const usable = height - PADDING_Y * 2;
    const step = col.length > 1 ? usable / (col.length - 1) : 0;
    col.forEach((n, i) => {
      positions[n.id] = {
        x: 80 + colIdx * COLUMN_GAP,
        y: col.length === 1 ? height / 2 : PADDING_Y + i * step,
      };
    });
  });

  return { width, height, positions };
}

export function KnowledgeNetwork() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<string>("");
  const [graph, setGraph] = useState<{
    nodes: GraphNode[];
    edges: GraphEdge[];
  }>({ nodes: [], edges: [] });
  const [hover, setHover] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<Set<GraphNode["type"]>>(
    new Set(TYPE_ORDER)
  );
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiFetch<Course[]>("/api/courses/").then(setCourses);
  }, []);

  useEffect(() => {
    setLoading(true);
    const qs = courseId ? `?course_id=${courseId}` : "";
    apiFetch<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
      `/api/knowledge/graph${qs}`
    )
      .then(setGraph)
      .catch((e) => alert(`Gagal memuat graph: ${e.message}`))
      .finally(() => setLoading(false));
  }, [courseId]);

  const filteredNodes = useMemo(
    () => graph.nodes.filter((n) => active.has(n.type)),
    [graph, active]
  );
  const visibleIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );
  const filteredEdges = useMemo(
    () =>
      graph.edges.filter(
        (e) => visibleIds.has(e.source) && visibleIds.has(e.target)
      ),
    [graph.edges, visibleIds]
  );

  const layout = useMemo(() => layoutGraph(filteredNodes), [filteredNodes]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const n of graph.nodes) c[n.type] = (c[n.type] || 0) + 1;
    return c;
  }, [graph]);

  const toggleType = (t: GraphNode["type"]) => {
    const next = new Set(active);
    if (next.has(t)) next.delete(t);
    else next.add(t);
    setActive(next);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        <div>
          <label className="text-xs font-medium text-slate-500 mb-1 block">
            Mata Kuliah
          </label>
          <select
            value={courseId}
            onChange={(e) => setCourseId(e.target.value)}
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">Semua Mata Kuliah</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap gap-2 ml-auto">
          {TYPE_ORDER.map((t) => (
            <button
              key={t}
              onClick={() => toggleType(t)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                active.has(t)
                  ? "bg-white border-slate-300 text-slate-700"
                  : "bg-slate-100 border-slate-200 text-slate-400"
              }`}
            >
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: TYPE_COLOR[t] }}
              />
              {TYPE_LABEL[t]}
              <span className="text-slate-400">({counts[t] || 0})</span>
            </button>
          ))}
        </div>
      </div>

      <div
        ref={wrapRef}
        className="relative rounded-2xl border border-slate-200 bg-white overflow-auto"
        style={{ height: "640px" }}
      >
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">
            Memuat knowledge graph…
          </div>
        ) : filteredNodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">
            Belum ada data. Mulai dengan membuat RPS atau mengunggah materi.
          </div>
        ) : (
          <svg
            width={layout.width}
            height={layout.height}
            className="block"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
            </defs>

            {/* Column labels */}
            {TYPE_ORDER.map((t, idx) => (
              <text
                key={`label-${t}`}
                x={80 + idx * 260}
                y={20}
                textAnchor="start"
                className="text-[11px] uppercase tracking-widest"
                fill="#94a3b8"
              >
                {TYPE_LABEL[t]}
              </text>
            ))}

            {/* Edges */}
            {filteredEdges.map((edge, i) => {
              const a = layout.positions[edge.source];
              const b = layout.positions[edge.target];
              if (!a || !b) return null;
              const midX = (a.x + b.x) / 2;
              return (
                <path
                  key={`e-${i}`}
                  d={`M ${a.x} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x} ${b.y}`}
                  fill="none"
                  stroke="#cbd5e1"
                  strokeWidth={1}
                  markerEnd="url(#arrow)"
                />
              );
            })}

            {/* Nodes */}
            {filteredNodes.map((n) => {
              const p = layout.positions[n.id];
              if (!p) return null;
              const isHover = hover?.id === n.id;
              const isAutoMaterial =
                n.type === "material" && Boolean(n.meta?.auto_generated);
              const fill = isAutoMaterial ? "#9333ea" : TYPE_COLOR[n.type];
              return (
                <g
                  key={n.id}
                  transform={`translate(${p.x}, ${p.y})`}
                  onMouseEnter={() => setHover(n)}
                  onMouseLeave={() => setHover(null)}
                  style={{ cursor: "pointer" }}
                >
                  {isAutoMaterial ? (
                    <rect
                      x={isHover ? -11 : -8}
                      y={isHover ? -11 : -8}
                      width={isHover ? 22 : 16}
                      height={isHover ? 22 : 16}
                      rx={3}
                      fill={fill}
                      stroke="white"
                      strokeWidth={2}
                    />
                  ) : (
                    <circle
                      r={isHover ? 11 : 8}
                      fill={fill}
                      stroke="white"
                      strokeWidth={2}
                    />
                  )}
                  <text
                    x={14}
                    y={4}
                    className="text-[11px]"
                    fill="#0f172a"
                  >
                    {n.label.length > 28
                      ? n.label.slice(0, 28) + "…"
                      : n.label}
                  </text>
                </g>
              );
            })}
          </svg>
        )}

        {hover && (
          <div className="pointer-events-none absolute top-3 right-3 max-w-xs rounded-xl border border-slate-200 bg-white/95 p-3 shadow-md">
            <div className="text-[10px] uppercase tracking-widest text-slate-400">
              {TYPE_LABEL[hover.type]}
            </div>
            <div className="text-sm font-semibold text-slate-800 mt-0.5">
              {hover.label}
            </div>
            {hover.meta && (
              <dl className="mt-2 space-y-0.5 text-xs text-slate-600">
                {Object.entries(hover.meta).map(([k, v]) =>
                  v == null || v === "" ? null : (
                    <div key={k} className="flex gap-1">
                      <dt className="text-slate-400 capitalize">{k}:</dt>
                      <dd className="flex-1 break-words">{String(v)}</dd>
                    </div>
                  )
                )}
              </dl>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
