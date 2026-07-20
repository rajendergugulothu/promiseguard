"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Workspace, type Candidate, type Commitment, type Alert } from "@/lib/api";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-600",
};

export default function WorkspaceDashboard() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [ws, setWs] = useState<Workspace | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    if (!id) return;
    api.workspaces.get(id).then(setWs).catch(console.error);
    api.candidates.list(id).then(setCandidates).catch(console.error);
    api.commitments.list(id).then(setCommitments).catch(console.error);
    api.alerts.list(id, true).then(setAlerts).catch(console.error);
  }, [id]);

  const openCommitments = commitments.filter(c => !["fulfilled", "missed"].includes(c.status));
  const atRisk = commitments.filter(c => c.status === "at_risk");
  const unowned = openCommitments.filter(c => !c.responsible_owner);

  const navItems = [
    { label: "AE Review Queue", path: "review", badge: candidates.length, color: "blue",
      desc: "Commitment candidates awaiting AE confirmation" },
    { label: "Commitment Ledger", path: "ledger", badge: openCommitments.length, color: "gray",
      desc: "All confirmed commitments across accounts" },
    { label: "Portfolio Dashboard", path: "portfolio", badge: atRisk.length, color: "orange",
      desc: "CCO view — ARR exposure and risk by account" },
    { label: "Legal Queue", path: "legal", badge: null, color: "red",
      desc: "Security and compliance commitments awaiting legal review" },
    { label: "Conflicts", path: "conflicts", badge: null, color: "yellow",
      desc: "Cross-customer and date-infeasible conflicts" },
    { label: "Alerts", path: "alerts", badge: alerts.length, color: "gray",
      desc: "Active alerts across all commitments" },
  ];

  return (
    <div>
      <div className="mb-8">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push("/")}>← All workspaces</div>
        <h1 className="text-2xl font-semibold">{ws?.name || "Loading…"}</h1>
        <div className="text-sm text-gray-400">{ws?.organisation}</div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Pending AE review", value: candidates.length, color: "text-blue-600" },
          { label: "Open commitments", value: openCommitments.length, color: "text-gray-900" },
          { label: "At risk", value: atRisk.length, color: "text-orange-600" },
          { label: "Unowned", value: unowned.length, color: "text-red-600" },
        ].map(m => (
          <div key={m.label} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
            <div className="text-xs text-gray-500 mt-1">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Navigation cards */}
      <div className="grid grid-cols-2 gap-4">
        {navItems.map(item => (
          <div key={item.path} onClick={() => router.push(`/workspace/${id}/${item.path}`)}
            className="bg-white border border-gray-200 rounded-lg p-5 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all flex items-start justify-between">
            <div>
              <div className="font-medium text-sm mb-1">{item.label}</div>
              <div className="text-xs text-gray-400">{item.desc}</div>
            </div>
            {item.badge !== null && item.badge > 0 && (
              <span className="bg-blue-600 text-white text-xs font-semibold rounded-full px-2 py-0.5 ml-3 mt-0.5">
                {item.badge}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
