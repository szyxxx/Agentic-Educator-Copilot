import { apiFetch } from "@/lib/api-server";
import Accounts from "./Accounts";
export default async function Page(){ const [users,courses]=await Promise.all([apiFetch<any[]>("/api/auth/users"),apiFetch<any[]>("/api/courses/")]);return <Accounts users={users} courses={courses}/>; }
