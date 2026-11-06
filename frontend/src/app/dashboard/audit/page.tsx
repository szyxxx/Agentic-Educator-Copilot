import { apiFetch } from "@/lib/api-server";
export default async function Audit({searchParams}:{searchParams:Promise<{offset?:string;action?:string}>}) {
  const query=await searchParams;const offset=Math.max(0,Number(query.offset)||0);
  const data=await apiFetch<any>(`/api/audit/?limit=50&offset=${offset}${query.action?`&action=${encodeURIComponent(query.action)}`:""}`);
  return <section className="space-y-5"><h1 className="text-3xl font-semibold">Jejak Audit</h1><p className="text-sm text-slate-600">{data.total} peristiwa. Versi objek meningkat pada setiap perubahan; model kosong berarti tidak ada panggilan LLM yang tercatat pada operasi itu.</p>
    <form className="flex gap-3"><label className="text-sm">Aksi<input name="action" defaultValue={query.action} placeholder="Contoh: approve, grade_edit" className="ml-2 rounded-lg border p-2"/></label><button className="rounded-lg border px-4">Saring</button></form>
    <div className="overflow-x-auto rounded-2xl border bg-white"><table className="w-full text-left text-xs"><thead><tr>{["Waktu UTC","Pelaku","Aksi","Objek","Versi","Model LLM"].map(h=><th key={h} className="p-3">{h}</th>)}</tr></thead><tbody>{data.events.map((e:any)=><tr key={e.id} className="border-t align-top"><td className="p-3">{e.occurred_at}</td><td className="p-3">{e.actor_name}<br/>{e.actor_role}</td><td className="p-3">{e.action}</td><td className="max-w-xs break-all p-3">{e.object_type}/{e.object_id}</td><td className="p-3">{e.version}<br/><span title="Versi aplikasi">{e.application_version}</span></td><td className="p-3">{e.llm_model??"—"}</td></tr>)}</tbody></table></div>
    <div className="flex gap-5">{offset>0&&<a href={`?offset=${Math.max(0,offset-50)}&action=${encodeURIComponent(query.action??"")}`}>Sebelumnya</a>}{offset+50<data.total&&<a href={`?offset=${offset+50}&action=${encodeURIComponent(query.action??"")}`}>Berikutnya</a>}</div>
  </section>;
}
