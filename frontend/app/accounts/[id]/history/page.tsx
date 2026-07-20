"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useParams } from "next/navigation";
import { api } from "@/lib/api";

export default function AccountHistory() {
  const { id: accountId } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get("workspace_id") || "";
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (accountId && workspaceId) {
      api.reports.history(accountId as string, workspaceId).then(setData).catch(console.error);
    }
  }, [accountId, workspaceId]);

  if (!data) return <div className="text-gray-400 text-sm">Loading account history…</div>;

  const byStatus: Record<string, any[]> = {};
  data.commitments?.forEach((c: any) => {
    byStatus[c.status] = byStatus[c.status] || [];
    byStatus[c.status].push(c);
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Account History</h1>
        <p className="text-sm text-gray-400 mt-0.5">Full commitment ledger for {accountId} · {data.total} total</p>
        <div className="mt-1 text-xs text-gray-400">
          This view survives CSM reassignment. Use it to onboard a new CSM to account history.
        </div>
      </div>

      {Object.entries(byStatus).map(([status, items]) => (
        <div key={status} className="mb-6">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">{status.replace("_", " ")} ({items.length})</h2>
          <div className="space-y-2">
            {items.map((c: any) => (
              <div key={c.id} className="bg-white border border-gray-100 rounded px-4 py-3">
                <div className="text-sm text-gray-800">{c.statement}</div>
                <div className="text-xs text-gray-400 mt-1 flex gap-3 flex-wrap">
                  <span>{c.type}</span>
                  {c.owner && <span>Owner: {c.owner}</span>}
                  {c.due_date && <span>Due: {c.due_date}</span>}
                  {c.fulfilled_at && <span className="text-green-600">Fulfilled: {new Date(c.fulfilled_at).toLocaleDateString()}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
