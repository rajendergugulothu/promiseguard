"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type LegalReview } from "@/lib/api";

export default function LegalQueue() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [reviews, setReviews] = useState<LegalReview[]>([]);
  const [reviewer, setReviewer] = useState("");

  useEffect(() => {
    if (id) api.legal.queue(id as string).then(setReviews).catch(console.error);
  }, [id]);

  async function adjudicate(reviewId: string, decision: string) {
    if (!reviewer) return alert("Enter your name first");
    await api.legal.adjudicate(reviewId, { reviewer, decision });
    api.legal.queue(id as string).then(setReviews);
  }

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">Legal Review Queue</h1>
        <p className="text-sm text-gray-400 mt-0.5">Security, compliance, and data-residency commitments awaiting legal approval</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600 whitespace-nowrap">Reviewing as:</label>
        <input value={reviewer} onChange={e => setReviewer(e.target.value)}
          placeholder="legal.reviewer@company.com"
          className="flex-1 border border-gray-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
      </div>

      {reviews.length === 0 && (
        <div className="text-gray-400 text-sm py-8 text-center">No pending legal reviews.</div>
      )}

      <div className="space-y-3">
        {reviews.map(r => (
          <div key={r.id} className="bg-white border border-red-200 rounded-lg p-5">
            <div className="text-xs text-red-600 font-medium mb-2">⚖️ SECURITY / COMPLIANCE</div>
            <div className="text-sm text-gray-500 mb-1">Commitment ID: {r.commitment_id}</div>
            <div className="text-xs text-gray-400 mb-4">Status: {r.status}</div>
            <div className="flex gap-2">
              <button onClick={() => adjudicate(r.id, "approved")}
                className="bg-green-600 text-white text-sm px-4 py-1.5 rounded hover:bg-green-700">
                Approve
              </button>
              <button onClick={() => adjudicate(r.id, "rejected")}
                className="bg-red-600 text-white text-sm px-4 py-1.5 rounded hover:bg-red-700">
                Reject
              </button>
              <button onClick={() => adjudicate(r.id, "escalated")}
                className="bg-white border border-gray-300 text-gray-700 text-sm px-4 py-1.5 rounded hover:bg-gray-50">
                Escalate to General Counsel
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
