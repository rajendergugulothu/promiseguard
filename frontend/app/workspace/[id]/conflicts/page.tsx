"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Conflict } from "@/lib/api";

const CONFLICT_LABELS: Record<string, { label: string; color: string }> = {
  cross_customer:     { label: "Cross-customer",   color: "bg-purple-100 text-purple-700" },
  cross_document:     { label: "Cross-document",   color: "bg-blue-100 text-blue-700" },
  date_infeasible:    { label: "Date infeasible",  color: "bg-orange-100 text-orange-700" },
  capability_gap:     { label: "Capability gap",   color: "bg-red-100 text-red-700" },
  self_contradiction: { label: "Self-contradiction", color: "bg-yellow-100 text-yellow-700" },
};

export default function Conflicts() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [resolver, setResolver] = useState("");

  useEffect(() => {
    if (id) api.conflicts.list(id as string, "open").then(setConflicts).catch(console.error);
  }, [id]);

  async function resolve(conflictId: string, dismissed = false) {
    if (!resolver) return alert("Enter your name first");
    await api.conflicts.resolve(conflictId, {
      resolved_by: resolver,
      resolution_notes: dismissed ? "Dismissed — not a real conflict" : "Resolved by account team",
    });
    api.conflicts.list(id as string, "open").then(setConflicts);
  }

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">Conflicts</h1>
        <p className="text-sm text-gray-400 mt-0.5">{conflicts.length} open conflict{conflicts.length !== 1 ? "s" : ""}</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Resolving as:</label>
        <input value={resolver} onChange={e => setResolver(e.target.value)}
          placeholder="your.email@company.com"
          className="flex-1 border border-gray-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
      </div>

      {conflicts.length === 0 && <div className="text-gray-400 text-sm py-8 text-center">No open conflicts.</div>}

      <div className="space-y-3">
        {conflicts.map(c => {
          const meta = CONFLICT_LABELS[c.conflict_type] || { label: c.conflict_type, color: "bg-gray-100 text-gray-600" };
          return (
            <div key={c.id} className="bg-white border border-gray-200 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${meta.color}`}>{meta.label}</span>
              </div>
              <div className="text-sm text-gray-700 mb-3">{c.description}</div>
              <div className="text-xs text-gray-400 mb-3">
                Commitment A: {c.commitment_a_id}
                {c.commitment_b_id && <> · Commitment B: {c.commitment_b_id}</>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => resolve(c.id)}
                  className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded hover:bg-blue-700">Mark resolved</button>
                <button onClick={() => resolve(c.id, true)}
                  className="bg-white border border-gray-300 text-gray-600 text-sm px-3 py-1.5 rounded hover:bg-gray-50">Dismiss</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
