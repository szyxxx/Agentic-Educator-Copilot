"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

export default function ApproveButton({
  rpsId,
  status,
}: {
  rpsId: string;
  status: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (status === "compliant" || status === "validated") return null;

  const handleApprove = async () => {
    setLoading(true);
    try {
      await apiFetch(`/api/rps/${rpsId}/approve`, { method: "POST" });
      router.refresh();
    } catch (e: any) {
      alert(`Gagal menyetujui: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={handleApprove}
      disabled={loading}
      className="bg-teal-600 hover:bg-teal-700 text-white"
    >
      {loading ? "Menyimpan..." : "✓ Approve RPS"}
    </Button>
  );
}
