import { CoursesView } from "./CoursesView";
import { apiFetch } from "@/lib/api-server";

export default async function CoursesPage() {
  const data = await apiFetch<any>("/api/dashboard/courses");
  return <CoursesView data={data} />;
}
