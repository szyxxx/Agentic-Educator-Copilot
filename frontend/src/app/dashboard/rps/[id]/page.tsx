import Link from "next/link";
import ReactMarkdown from "react-markdown";
import ApproveButton from "./ApproveButton";
import ComplianceReport from "./ComplianceReport";
import FillMissingButton from "./FillMissingButton";
import FindingsPanel from "./FindingsPanel";
import MeetingsTable from "./MeetingsTable";
import OverallFeedback from "./OverallFeedback";

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

export default async function RPSDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  let data: any;
  try {
    data = await apiFetch<any>(`/api/dashboard/rps/${resolvedParams.id}`);
  } catch {
    data = null;
  }

  if (!data || !data.summary) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold">RPS Tidak Ditemukan</h1>
        <p className="mt-2 text-slate-500">RPS ini mungkin telah dihapus atau ID tidak valid.</p>
        <Link href="/dashboard/rps" className="mt-4 inline-block">
          <Button>Kembali ke Daftar</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
            Detail RPS
          </p>
          <h1 className="text-3xl font-semibold">{data.course}</h1>
          <p className="mt-1 text-sm text-slate-500">{data.details}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/dashboard/rps">
            <Button variant="outline">Kembali</Button>
          </Link>
          <Link href={`/dashboard/rps/${resolvedParams.id}/edit`}>
            <Button variant="ghost">Edit</Button>
          </Link>
          <FillMissingButton
            rpsId={resolvedParams.id}
            status={data.status || "draft"}
          />
          <ApproveButton rpsId={resolvedParams.id} status={data.status || "draft"} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Capaian Pembelajaran</CardTitle>
            <CardDescription>CPL dan CPMK mata kuliah</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-sm text-slate-800 mb-2">Capaian Pembelajaran Lulusan (CPL)</h3>
                <ul className="list-disc pl-5 text-sm text-slate-600 space-y-2">
                  {data.cpl_list?.map((cpl: string, idx: number) => (
                    <li key={idx}>
                      <span className="font-semibold text-teal-700 mr-1">CPL-{idx + 1}:</span> 
                      <span className="inline [&>p]:inline"><ReactMarkdown>{cpl}</ReactMarkdown></span>
                    </li>
                  ))}
                  {(!data.cpl_list || data.cpl_list.length === 0) && (
                    <li className="text-slate-400 italic">Belum ada CPL.</li>
                  )}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-800 mb-2">Capaian Pembelajaran Mata Kuliah (CPMK)</h3>
                <ul className="list-disc pl-5 text-sm text-slate-600 space-y-2">
                  {data.cpmk_list?.map((cpmk: string, idx: number) => (
                    <li key={idx}>
                      <span className="font-semibold text-indigo-700 mr-1">CPMK-{idx + 1}:</span> 
                      <span className="inline [&>p]:inline"><ReactMarkdown>{cpmk}</ReactMarkdown></span>
                    </li>
                  ))}
                  {(!data.cpmk_list || data.cpmk_list.length === 0) && (
                    <li className="text-slate-400 italic">Belum ada CPMK.</li>
                  )}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Referensi & Pustaka</CardTitle>
            <CardDescription>Sumber referensi utama dan pendukung</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 text-sm text-slate-700 space-y-2">
              {data.references_list?.map((ref: string, idx: number) => (
                <li key={idx}>
                  {ref.startsWith("http") ? (
                    <a href={ref} target="_blank" rel="noreferrer" className="text-teal-600 hover:underline">{ref}</a>
                  ) : (
                    ref
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Bahan Kajian</CardTitle>
            <CardDescription>Pokok bahasan yang dicakup mata kuliah</CardDescription>
          </CardHeader>
          <CardContent>
            {(data.bahan_kajian || []).length === 0 ? (
              <p className="text-sm text-slate-400 italic">Belum ada bahan kajian.</p>
            ) : (
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                {data.bahan_kajian.map((b: string, idx: number) => (
                  <li key={idx}>{b}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Metode & Modalitas</CardTitle>
            <CardDescription>Strategi pembelajaran tingkat mata kuliah</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Metode Pembelajaran
              </p>
              {(data.learning_methods || []).length === 0 ? (
                <p className="text-sm text-slate-400 italic">Belum ditentukan.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {data.learning_methods.map((m: string, idx: number) => (
                    <Badge key={idx} variant="outline">
                      {m}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Modalitas
              </p>
              <p className="text-sm text-slate-700">
                {data.learning_modality || (
                  <span className="text-slate-400 italic">Belum ditentukan.</span>
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {data.summary.map((item: any) => (
          <Card key={item.label}>
            <CardHeader className="pb-2">
              <CardDescription>{item.label}</CardDescription>
              <CardTitle className="text-3xl">{item.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-xs text-slate-500">{item.note}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      <OverallFeedback
        rpsId={resolvedParams.id}
        initialFeedback={data.feedback || ""}
        status={data.status || "draft"}
      />

      <FindingsPanel rpsId={resolvedParams.id} />

      <ComplianceReport rpsId={resolvedParams.id} />

      <Card>
        <CardHeader>
          <CardTitle>Rencana 16 Pertemuan</CardTitle>
          <CardDescription>
            Format institusi: Modul, Bahan Kajian/Topik, Sub-Topik, CPMK Terkait, dan No. Referensi.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <MeetingsTable
            rpsId={resolvedParams.id}
            courseId={data.course_id || ""}
            meetings={data.meetings}
            referencesList={data.references_list || []}
            cpmkList={data.cpmk_list || []}
            rpsStatus={data.status || "draft"}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Daftar Referensi (Bernomor)</CardTitle>
          <CardDescription>
            Nomor di kolom "No. Referensi" merujuk ke daftar di sini.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {(data.references_list || []).length === 0 ? (
            <p className="text-sm text-slate-400 italic">Belum ada referensi.</p>
          ) : (
            <ol className="list-decimal pl-5 text-sm text-slate-700 space-y-1">
              {data.references_list.map((ref: string, idx: number) => (
                <li key={idx}>
                  {ref.startsWith("http") ? (
                    <a
                      href={ref}
                      target="_blank"
                      rel="noreferrer"
                      className="text-teal-600 hover:underline"
                    >
                      {ref}
                    </a>
                  ) : (
                    ref
                  )}
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
