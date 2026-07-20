"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Alert } from "@/lib/api";

const TRIGGER_LABEL: Record<string, string> = {
  deadline_30d: "Deadline in 30 days",   deadline_7d: "Deadline in 7 days",
  deadline_1d: "Deadline tomorrow",       dependency_slipped: "Dependency slipped",
  new_conflict: "New conflict detected",  status_at_risk: "Status: at risk",
  high_risk_unowned: "High risk & unowned", commitment_missed: "Commitment missed",
};

export default function Alerts() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    if (id) api.alerts.list(id as string).then(setAlerts).catch(console.error);
  }, [id]);

  async function ack(alertId: string) {
    await api.alerts.acknowledge(alertId, "Reviewed");
    api.alerts.list(id as string).then(setAlerts);
  }

  const unacked = alerts.filter(a => !a.acknowledged_at);
  const acked = alerts.filter(a => a.acknowledged_at);

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">Alerts</h1>
        <p className="text-sm text-gray-400 mt-0.5">{unacked.length} unacknowledged</p>
      </div>

      {unacked.length === 0 && <div className="text-gray-400 text-sm py-4 text-center">No unacknowledged alerts.</div>}

      <div className="space-y-2 mb-6">
        {unacked.map(a => (
          <div key={a.id} className="bg-orange-50 border border-orange-200 rounded-lg px-5 py-3 flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-orange-700">{TRIGGER_LABEL[a.trigger_type] || a.trigger_type}</div>
              <div className="text-sm text-gray-700 mt-0.5">{a.message}</div>
              <div className="text-xs text-gray-400 mt-0.5">To: {a.recipient}</div>
            </div>
            <button onClick={() => ack(a.id)}
              className="ml-4 text-xs text-gray-500 border border-gray-200 rounded px-3 py-1 hover:bg-white whitespace-nowrap">
              Acknowledge
            </button>
          </div>
        ))}
      </div>

      {acked.length > 0 && (
        <div>
          <h2 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">Acknowledged</h2>
          <div className="space-y-1">
            {acked.map(a => (
              <div key={a.id} className="bg-white border border-gray-100 rounded px-4 py-2 flex items-center justify-between opacity-60">
                <div className="text-xs text-gray-500">{a.message}</div>
                <div className="text-xs text-gray-300 ml-4 whitespace-nowrap">
                  {new Date(a.acknowledged_at!).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
