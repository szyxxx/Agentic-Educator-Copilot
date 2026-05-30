import { KnowledgeHub } from "./KnowledgeHub";
import { apiFetch } from "@/lib/api";

export default async function KnowledgeHubPage() {
  const [data, courses] = await Promise.all([
    apiFetch<any>("/api/dashboard/knowledge-base"),
    apiFetch<any[]>("/api/courses/"),
  ]);
  return <KnowledgeHub data={data} courses={courses} />;
}
