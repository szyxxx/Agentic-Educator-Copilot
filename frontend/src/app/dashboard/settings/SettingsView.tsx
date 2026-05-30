"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type Profile = {
  name: string;
  email: string;
  institution: string;
  semester: string;
};

type Notification = { id: string; label: string; enabled: boolean };

type SystemEntry = { label: string; value: string };

type Props = {
  initialData: {
    profile: Profile;
    notifications: Notification[];
    system: SystemEntry[];
  };
};

export function SettingsView({ initialData }: Props) {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile>(initialData.profile);
  const [notifications, setNotifications] = useState<Notification[]>(
    initialData.notifications
  );
  const [savingProfile, setSavingProfile] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  const updateProfile = async () => {
    setSavingProfile(true);
    try {
      await apiFetch("/api/settings/profile", {
        method: "PUT",
        json: profile,
      });
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 2000);
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyimpan profil: ${e.message}`);
    } finally {
      setSavingProfile(false);
    }
  };

  const toggleNotif = async (id: string, enabled: boolean) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, enabled } : n))
    );
    try {
      await apiFetch("/api/settings/notifications", {
        method: "PUT",
        json: { id, enabled },
      });
    } catch (e: any) {
      alert(`Gagal menyimpan toggle: ${e.message}`);
      // Revert
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, enabled: !enabled } : n))
      );
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">⚙️ Pengaturan Akun & Sistem</h1>
        <p className="mt-1 text-sm text-slate-500">
          Profil dosen, preferensi notifikasi, dan parameter AI yang dipakai oleh sistem.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Profil Dosen</CardTitle>
            <CardDescription>
              Identitas yang ditampilkan di dashboard dan dokumen RPS.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Field
              label="Nama Lengkap"
              value={profile.name}
              onChange={(v) => setProfile({ ...profile, name: v })}
            />
            <Field
              label="Email"
              type="email"
              value={profile.email}
              onChange={(v) => setProfile({ ...profile, email: v })}
            />
            <Field
              label="Institusi / Perguruan Tinggi"
              value={profile.institution}
              onChange={(v) => setProfile({ ...profile, institution: v })}
            />
            <Field
              label="Semester Aktif"
              value={profile.semester}
              onChange={(v) => setProfile({ ...profile, semester: v })}
              placeholder="Contoh: Semester Genap 2025/2026"
            />
            <div className="flex items-center justify-between pt-2">
              {savedFlash && (
                <span className="text-xs text-emerald-600">Tersimpan ✓</span>
              )}
              <Button onClick={updateProfile} disabled={savingProfile} className="ml-auto">
                {savingProfile ? "Menyimpan..." : "Simpan Profil"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preferensi Notifikasi</CardTitle>
            <CardDescription>
              Notifikasi yang ingin Anda terima — perubahan langsung tersimpan.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {notifications.map((item) => (
              <label
                key={item.id}
                className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm cursor-pointer"
              >
                <span className="text-slate-700">{item.label}</span>
                <input
                  type="checkbox"
                  checked={item.enabled}
                  onChange={(e) => toggleNotif(item.id, e.target.checked)}
                  className="h-4 w-4 accent-teal-600"
                />
              </label>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Konfigurasi AI & Sistem</CardTitle>
          <CardDescription>
            Parameter aktif untuk RPS Generator dan Auto-Grading.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {initialData.system.map((item) => (
            <div key={item.label}>
              <p className="text-xs text-slate-500">{item.label}</p>
              <p className="text-sm font-medium text-slate-900">{item.value}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-500 mb-1 block">
        {label}
      </label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 border rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/40"
      />
    </div>
  );
}
