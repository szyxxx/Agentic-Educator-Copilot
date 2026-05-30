import { SettingsView } from "./SettingsView";
import { apiFetch } from "@/lib/api";

export default async function SettingsPage() {
  const data = await apiFetch<any>("/api/dashboard/settings");
  return <SettingsView initialData={data} />;
}
