"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useIdentity } from "@/components/SessionProvider";
import type { Submission } from "./Submissions";
export default function GradeReview({submission:s,questions,onChange}:{submission:Submission;questions:any[];onChange:()=>Promise<void>}) {
  const user=useIdentity();
  const essays=(s.question_scores?.length?s.question_scores:questions.map(q=>({id:q.id,type:q.type,score:null,max_score:q.max_score??30,feedback:"",source:"human"}))).filter(q=>q.type==="essay");
  const [draft,setDraft]=useState(essays.map(q=>({...q,scoreText:q.score==null?"":String(q.score)})));
  const [note,setNote]=useState(s.review_note??"");const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  if (!essays.length) return null;
  const canReview=user?.role==="admin"||user?.role==="dosen";
  const submit=async(approve:boolean)=>{setBusy(true);setError("");try{
    if(approve) await apiFetch(`/api/grading/submissions/${s.id}/approve`,{method:"POST",json:{version:s.version,note}});
    else {
      const valid=draft.filter(q=>q.scoreText.trim()!=="");
      if(!valid.length)throw new Error("Isi setidaknya satu skor esai.");
      await apiFetch(`/api/grading/submissions/${s.id}/review`,{method:"PATCH",json:{version:s.version,note,essay_scores:valid.map(q=>({id:q.id,score:Number(q.scoreText),feedback:q.feedback}))}});
    }
    await onChange();
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  return <details className="mt-3 min-w-72 max-w-xl rounded-xl border bg-slate-50 p-3 text-left"><summary className="cursor-pointer font-medium">Tinjau nilai esai · Versi {s.version}</summary>
    <p className="my-2 text-xs">Usulan {s.proposed_score??"belum lengkap"} / 100. Nilai final {s.score??"belum ditetapkan"}.</p>
    {draft.map((q,i)=><div key={q.id} className="my-3 space-y-2 border-t pt-3"><p className="font-medium">{q.id}: {questions.find(item=>item.id===q.id)?.question}</p><p className="whitespace-pre-wrap text-xs">Jawaban: {s.answers?.[q.id]||"(kosong)"}</p><p className="text-xs">Sumber: {q.source} · Model: {s.grading_model??"—"}</p>
      <label className="block text-xs">Skor (0–{q.max_score})<input aria-label={`Skor ${q.id}`} type="number" min={0} max={q.max_score} step="0.1" disabled={!canReview||busy} value={q.scoreText} onChange={e=>setDraft(d=>d.map((x,j)=>j===i?{...x,scoreText:e.target.value}:x))} className="ml-2 w-24 rounded border p-2"/></label>
      <label className="block text-xs">Feedback<textarea aria-label={`Feedback ${q.id}`} disabled={!canReview||busy} value={q.feedback} onChange={e=>setDraft(d=>d.map((x,j)=>j===i?{...x,feedback:e.target.value}:x))} className="mt-1 w-full rounded border p-2"/></label>
    </div>)}
    <label className="block text-xs">Catatan tinjauan<textarea value={note} disabled={!canReview||busy} onChange={e=>setNote(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
    {s.reviewed_by&&<p className="my-2 text-xs">Disetujui oleh {s.reviewed_by} pada {s.reviewed_at}.</p>}
    {error&&<p role="alert" className="my-2 text-xs text-rose-700">{error}</p>}
    {canReview&&<div className="mt-3 flex flex-wrap gap-2"><Button size="sm" variant="outline" disabled={busy} onClick={()=>submit(false)}>Simpan perubahan skor</Button><Button size="sm" disabled={busy||s.status!=="needs_review"||s.proposed_score==null||draft.some((q,i)=>q.scoreText!==(essays[i].score==null?"":String(essays[i].score))||q.feedback!==essays[i].feedback)||note!==(s.review_note??"")} onClick={()=>submit(true)}>Setujui nilai tersimpan</Button></div>}
    <p className="mt-2 text-xs text-slate-500">Simpan perubahan lebih dahulu, lalu setujui versi tersimpan. Persetujuan dicatat pada audit.</p>
  </details>;
}
