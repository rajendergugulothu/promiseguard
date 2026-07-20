"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function Portfolio() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (id) api.reports.portfolio(id as string).then(setData).catch(console.error);
  }, [id]);

  if (!data) return <div className="text-gray-400 text-sm">Loading portfolio…</div>;

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">Portfolio Risk Dashboard</h1>
        <p className="text-sm text-gray-400 mt-0.5">CCO view — commitment risk across all accounts</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-gray-900">{data.total_open_commitments}</div>
          <div className="text-xs text-gray-500 mt-1">Open commitments</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">{data.accounts_at_risk}</div>
          <div className="text-xs text-gray-500 mt-1">Accounts with open commitments</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600">${(data.total_arr_exposure || 0).toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Total ARR exposure</div>
        </div>
      </div>

      {/* By account */}
      <h2 className="text-sm font-semibold text-gray-700 mb-3">By account — sorted by ARR exposure</h2>
      <div className="space-y-2">
        {data.accounts?.map((a: any) => (
          <div key={a.account_id} className="bg-white border border-gray-200 rounded-lg px-5 py-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-sm">{a.account_name}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {a.total_commitments} commitment{a.total_commitments !== 1 ? "s" : ""}
                  {a.unowned > 0 && <span className="text-red-500 ml-2">· {a.unowned} unowned</span>}
                  {a.critical_count > 0 && <span className="text-red-600 ml-2 font-medium">· {a.critical_count} critical</span>}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">${a.total_arr_exposure.toLocaleString()}</div>
                <div className="text-xs text-gray-400">ARR exposure</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
