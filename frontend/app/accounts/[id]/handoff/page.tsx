"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useParams } from "next/navigation";
import { api } from "@/lib/api";

export default function HandoffReport() {
  const { id: accountId } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get("workspace_id") || "";
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (accountId && workspaceId) {
      api.reports.handoff(accountId as string, workspaceId).then(setData).catch(console.error);
    }
  }, [accountId, workspaceId]);

  if (!data) return <div className="text-gray-400 text-sm">Generating handoff report…</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Commitment Handoff Report</h1>
        <p className="text-sm text-gray-400 mt-0.5">Review before the implementation kickoff call · Account: {accountId}</p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 text-sm text-amber-800">
        {data.note}
      </div>

      {/* Risk summary */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: "Total commitments", value: data.total_commitments },
          { label: "Unowned", value: data.summary?.unowned, warn: data.summary?.unowned > 0 },
          { label: "Pending legal review", value: data.summary?.pending_legal_review, warn: data.summary?.pending_legal_review > 0 },
          { label: "Unsupported capability", value: data.summary?.unsupported_capability, warn: data.summary?.unsupported_capability > 0 },
        ].map(m => (
          <div key={m.label} className={`border rounded-lg p-3 ${m.warn ? "bg-red-50 border-red-200" : "bg-white border-gray-200"}`}>
            <div className={`text-xl font-bold ${m.warn ? "text-red-600" : "text-gray-900"}`}>{m.value ?? 0}</div>
            <div className="text-xs text-gray-500 mt-0.5">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Risk items */}
      {Object.entries(data.risk_items || {}).map(([key, items]: any) => {
        if (!items?.length) return null;
        return (
          <div key={key} className="mb-6">
            <h2 className="text-sm font-semibold text-red-700 mb-2 uppercase tracking-wide">
              ⚠ {key.replace(/_/g, " ")} ({items.length})
            </h2>
            <div className="space-y-2">
              {items.map((c: any) => (
                <div key={c.id} className="bg-white border border-red-100 rounded-lg px-4 py-3">
                  <div className="text-sm text-gray-800">{c.statement}</div>
                  <div className="text-xs text-gray-400 mt-1 flex gap-3 flex-wrap">
                    <span className="font-medium text-red-500">{c.flags?.join(" · ")}</span>
                    {c.due_date && <span>Due: {c.due_date} ({c.due_date_confidence})</span>}
                    <span>Capability: {c.capability_status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* Standard commitments */}
      {data.standard_commitments?.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            Standard commitments ({data.standard_commitments.length})
          </h2>
          <div className="space-y-2">
            {data.standard_commitments.map((c: any) => (
              <div key={c.id} className="bg-white border border-gray-100 rounded px-4 py-3">
                <div className="text-sm text-gray-800">{c.statement}</div>
                <div className="text-xs text-gray-400 mt-1 flex gap-3">
                  {c.owner && <span>Owner: {c.owner}</span>}
                  {c.due_date && <span>Due: {c.due_date}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
