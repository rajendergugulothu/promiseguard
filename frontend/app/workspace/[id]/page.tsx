"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Workspace, type Candidate, type Commitment, type Alert } from "@/lib/api";

const NAV_ITEMS = [
  { label: "AE Review Queue", path: "review", icon: "🔍", desc: "Candidates awaiting confirmation before entering the ledger", badgeColor: "bg-blue-600" },
  { label: "Commitment Ledger", path: "ledger", icon: "📋", desc: "All confirmed commitments across accounts", badgeColor: "bg-gray-500" },
  { label: "Portfolio Dashboard", path: "portfolio", icon: "📊", desc: "CCO view — ARR exposure and risk by account", badgeColor: "bg-orange-500" },
  { label: "Legal Queue", path: "legal", icon: "⚖️", desc: "Security and compliance commitments awaiting legal review", badgeColor: "bg-red-500" },
  { label: "Conflicts", path: "conflicts", icon: "⚠️", desc: "Cross-customer and date-infeasible conflicts", badgeColor: "bg-yellow-500" },
  { label: "Alerts", path: "alerts", icon: "🔔", desc: "Active alerts across all commitments", badgeColor: "bg-gray-500" },
];

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

  const badges: Record<string, number> = {
    review: candidates.length,
    ledger: openCommitments.length,
    portfolio: atRisk.length,
    alerts: alerts.length,
  };

  const metrics = [
    { label: "Pending review", value: candidates.length, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-100" },
    { label: "Open commitments", value: openCommitments.length, color: "text-gray-900", bg: "bg-gray-50", border: "border-gray-200" },
    { label: "At risk", value: atRisk.length, color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-100" },
    { label: "Unowned", value: unowned.length, color: "text-red-600", bg: "bg-red-50", border: "border-red-100" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <button
        onClick={() => router.push("/")}
        className="text-xs text-gray-400 hover:text-gray-600 mb-6 flex items-center gap-1 transition-colors">
        ← All workspaces
      </button>

      {/* Page header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-base">
            {ws?.name?.charAt(0)?.toUpperCase() ?? "…"}
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{ws?.name ?? "Loading…"}</h1>
            <div className="text-xs text-gray-400">{ws?.organisation}</div>
          </div>
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        {metrics.map(m => (
          <div key={m.label} className={`${m.bg} border ${m.border} rounded-xl p-4`}>
            <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
            <div className="text-xs text-gray-500 mt-1 font-medium">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Nav cards */}
      <div className="grid grid-cols-2 gap-3">
        {NAV_ITEMS.map(item => (
          <div
            key={item.path}
            onClick={() => router.push(`/workspace/${id}/${item.path}`)}
            className="bg-white border border-gray-200 rounded-xl p-5 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all flex items-start justify-between group">
            <div className="flex items-start gap-3">
              <span className="text-xl mt-0.5">{item.icon}</span>
              <div>
                <div className="font-medium text-sm text-gray-900 group-hover:text-blue-600 transition-colors">{item.label}</div>
                <div className="text-xs text-gray-400 mt-0.5 leading-relaxed">{item.desc}</div>
              </div>
            </div>
            {badges[item.path] > 0 && (
              <span className={`${item.badgeColor} text-white text-xs font-semibold rounded-full px-2 py-0.5 ml-3 mt-0.5 shrink-0`}>
                {badges[item.path]}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
