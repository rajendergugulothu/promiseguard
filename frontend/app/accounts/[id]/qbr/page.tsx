"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  proposed: "text-gray-500", confirmed: "text-blue-600", in_progress: "text-indigo-600",
  at_risk: "text-orange-600", fulfilled: "text-green-600", disputed: "text-yellow-600", missed: "text-red-600",
};

export default function QBRView() {
  const { id: accountId } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get("workspace_id") || "";
  const router = useRouter();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (accountId && workspaceId) {
      api.reports.qbrView(accountId as string, workspaceId).then(setData).catch(console.error);
    }
  }, [accountId, workspaceId]);

  if (!data) return <div className="text-gray-400 text-sm">Loading QBR view…</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold">QBR Prep View</h1>
        <p className="text-sm text-gray-400 mt-0.5">Account: {accountId}</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: "Total open", value: data.total, color: "text-gray-900" },
          { label: "Overdue", value: data.overdue, color: "text-red-600" },
          { label: "Unowned", value: data.unowned, color: "text-orange-600" },
          { label: "With conflicts", value: data.with_open_conflicts, color: "text-yellow-600" },
        ].map(m => (
          <div key={m.label} className="bg-white border border-gray-200 rounded-lg p-3">
            <div className={`text-xl font-bold ${m.color}`}>{m.value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{m.label}</div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        {data.commitments?.map((c: any) => (
          <div key={c.id} className={`bg-white border rounded-lg px-5 py-4 ${
            c.severity === "critical" ? "border-red-200" :
            c.severity === "high" ? "border-orange-200" : "border-gray-200"
          }`}>
            <div className="flex items-start gap-3">
              <span className={`text-xs font-bold uppercase ${
                c.severity === "critical" ? "text-red-600" :
                c.severity === "high" ? "text-orange-500" : "text-gray-400"
              }`}>{c.severity}</span>
              <span className={`text-xs ml-auto ${STATUS_COLOR[c.status] || "text-gray-500"}`}>
                {c.status.replace("_", " ")}
              </span>
            </div>
            <div className="mt-2 text-sm text-gray-900">{c.statement}</div>
            <div className="mt-2 flex gap-4 text-xs text-gray-400 flex-wrap">
              <span>Owner: {c.owner || <span className="text-red-500">unassigned</span>}</span>
              {c.due_date && <span>Due: {c.due_date}</span>}
              {c.risk_score && <span>Risk: {(c.risk_score * 100).toFixed(0)}%</span>}
              {c.has_open_conflict && <span className="text-yellow-600">⚠ Open conflict</span>}
              {c.legal_status === "pending" && <span className="text-red-500">⚖️ Awaiting legal</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
