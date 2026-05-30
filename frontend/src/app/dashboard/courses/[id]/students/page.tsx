import StudentsView from "./StudentsView";
import { apiFetch } from "@/lib/api";

type Course = {
  id: string;
  name: string;
  code: string;
  sks: number;
  semester: number;
  program_study: string;
};

export default async function CourseStudentsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const courses = await apiFetch<Course[]>("/api/courses/");
  const course = courses.find((c) => c.id === id);
  return <StudentsView courseId={id} course={course} />;
}
