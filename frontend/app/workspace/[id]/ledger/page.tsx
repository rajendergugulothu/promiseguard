"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Commitment, CommitmentStatus } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  proposed: "bg-gray-100 text-gray-600",
  confirmed: "bg-blue-100 text-blue-700",
  in_progress: "bg-indigo-100 text-indigo-700",
  at_risk: "bg-orange-100 text-orange-700",
  fulfilled: "bg-green-100 text-green-700",
  disputed: "bg-yellow-100 text-yellow-700",
  missed: "bg-red-100 text-red-700",
};

const SEV_COLOR: Record<string, string> = {
  critical: "text-red-600", high: "text-orange-500", medium: "text-yellow-600", low: "text-gray-400",
};

export default function Ledger() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const params = filter !== "all" ? { status: filter } : undefined;
    api.commitments.list(id as string, params).then(c => { setCommitments(c); setLoading(false); });
  }, [id, filter]);

  const filters = ["all", "proposed", "confirmed", "in_progress", "at_risk", "fulfilled", "missed"];

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">Commitment Ledger</h1>
        <p className="text-sm text-gray-400 mt-0.5">{commitments.length} commitments</p>
      </div>

      <div className="flex gap-2 mb-5 flex-wrap">
        {filters.map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filter === f ? "bg-blue-600 text-white border-blue-600" : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
            }`}>
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      {loading && <div className="text-gray-400 text-sm">Loading…</div>}
      {!loading && commitments.length === 0 && (
        <div className="text-gray-400 text-sm py-8 text-center">No commitments found.</div>
      )}

      <div className="space-y-2">
        {commitments.map(c => (
          <div key={c.id} className="bg-white border border-gray-200 rounded-lg px-5 py-4">
            <div className="flex items-start gap-3">
              <span className={`text-xs font-bold uppercase ${SEV_COLOR[c.severity_tier]}`}>{c.severity_tier}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[c.status]}`}>{c.status.replace("_", " ")}</span>
              <span className="text-xs text-gray-400 ml-auto">{c.account_name}</span>
            </div>
            <div className="mt-2 text-sm text-gray-900">{c.statement}</div>
            <div className="mt-2 flex gap-4 text-xs text-gray-400">
              {c.responsible_owner && <span>Owner: {c.responsible_owner}</span>}
              {c.due_date && <span>Due: {c.due_date}</span>}
              {c.arr_exposure && <span>ARR: ${c.arr_exposure.toLocaleString()}</span>}
              {c.legal_review_status === "pending" && (
                <span className="text-red-500">⚖️ Awaiting legal review</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
