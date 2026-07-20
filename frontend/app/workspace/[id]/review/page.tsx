"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Candidate } from "@/lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-gray-100 text-gray-600 border-gray-200",
};

const TYPE_LABEL: Record<string, string> = {
  feature: "Feature delivery", date: "Date / milestone",
  pricing: "Pricing / commercial", security_compliance: "Security / compliance ⚖️",
  performance: "Performance", sla: "SLA / support",
  custom: "Custom", other: "Other",
};

export default function ReviewQueue() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState("");
  const [editedStatement, setEditedStatement] = useState("");
  const [dismissReason, setDismissReason] = useState("");
  const [owner, setOwner] = useState("");
  const [arr, setArr] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!id) return;
    api.candidates.list(id).then(c => { setCandidates(c); setLoading(false); }).catch(console.error);
  }, [id]);

  const remaining = candidates.filter(c => !done.has(c.id));
  const activeCandidate = active ? candidates.find(c => c.id === active) : null;

  async function submit(verdict: "confirmed" | "edited" | "dismissed") {
    if (!active || !reviewer) return;
    setSubmitting(true);
    try {
      await api.candidates.review(active, {
        verdict,
        reviewed_by: reviewer,
        edited_statement: verdict === "edited" ? editedStatement : undefined,
        dismiss_reason: verdict === "dismissed" ? dismissReason : undefined,
        responsible_owner: owner || undefined,
        arr_exposure: arr ? parseFloat(arr) : undefined,
      });
      setDone(prev => new Set([...prev, active]));
      setActive(null);
      setEditedStatement(""); setDismissReason(""); setOwner(""); setArr("");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="text-gray-400 text-sm">Loading candidates…</div>;

  return (
    <div>
      <div className="mb-6">
        <div className="text-xs text-gray-400 mb-1 cursor-pointer hover:underline" onClick={() => router.push(`/workspace/${id}`)}>← Dashboard</div>
        <h1 className="text-xl font-semibold">AE Review Queue</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          {remaining.length} candidate{remaining.length !== 1 ? "s" : ""} awaiting your review.
          Confirm, edit, or dismiss before commitments enter the ledger.
        </p>
      </div>

      {/* Reviewer name */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600 whitespace-nowrap">Reviewing as:</label>
        <input value={reviewer} onChange={e => setReviewer(e.target.value)}
          placeholder="your.email@company.com"
          className="flex-1 border border-gray-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
      </div>

      {remaining.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-green-700 font-medium">All candidates reviewed.</div>
          <div className="text-sm text-green-600 mt-1">Confirmed commitments are now in the ledger.</div>
        </div>
      )}

      <div className="space-y-3">
        {remaining.map(c => (
          <div key={c.id}
            className={`bg-white border rounded-lg overflow-hidden transition-all ${active === c.id ? "border-blue-400 shadow-sm" : "border-gray-200"}`}>

            {/* Card header */}
            <div className="px-5 py-4 cursor-pointer" onClick={() => setActive(active === c.id ? null : c.id)}>
              <div className="flex items-start gap-3">
                <span className={`text-xs font-medium px-2 py-0.5 rounded border ${SEVERITY_COLORS[c.severity_tier]}`}>
                  {c.severity_tier}
                </span>
                <span className="text-xs text-gray-400 mt-0.5">{TYPE_LABEL[c.commitment_type]}</span>
                <span className="ml-auto text-xs text-gray-300">{Math.round(c.extraction_confidence * 100)}% confidence</span>
              </div>
              <div className="mt-2 text-sm font-medium text-gray-900">{c.raw_statement}</div>
              {c.promisor && <div className="text-xs text-gray-400 mt-1">Said by: {c.promisor}</div>}
            </div>

            {/* Expanded review panel */}
            {active === c.id && (
              <div className="border-t border-gray-100 px-5 py-4 bg-gray-50 space-y-4">

                {/* Evidence */}
                <div>
                  <div className="text-xs font-medium text-gray-500 mb-1">Evidence passage</div>
                  <div className="bg-white border border-gray-200 rounded p-3 text-sm text-gray-700 italic">
                    "{c.evidence_passage}"
                  </div>
                  {c.evidence_location && (
                    <div className="text-xs text-gray-400 mt-1">Location: {c.evidence_location}</div>
                  )}
                </div>

                {c.classification_reason && (
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1">Why extracted as a commitment</div>
                    <div className="text-xs text-gray-600">{c.classification_reason}</div>
                  </div>
                )}

                {c.commitment_type === "security_compliance" && (
                  <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700">
                    ⚖️ <strong>Security / compliance tier.</strong> If confirmed, this commitment will route to the legal review queue before entering the ledger.
                  </div>
                )}

                {/* Optional fields */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Assign owner (optional)</label>
                    <input value={owner} onChange={e => setOwner(e.target.value)}
                      placeholder="owner@company.com"
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">ARR exposure ($)</label>
                    <input value={arr} onChange={e => setArr(e.target.value)} type="number"
                      placeholder="e.g. 120000"
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400" />
                  </div>
                </div>

                {/* Edit statement field */}
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Edit statement (if needed)</label>
                  <textarea value={editedStatement || c.raw_statement}
                    onChange={e => setEditedStatement(e.target.value)} rows={2}
                    className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400" />
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 pt-1">
                  <button onClick={() => submit(editedStatement && editedStatement !== c.raw_statement ? "edited" : "confirmed")}
                    disabled={!reviewer || submitting}
                    className="bg-green-600 text-white text-sm px-4 py-2 rounded hover:bg-green-700 disabled:opacity-40 font-medium">
                    ✓ Confirm
                  </button>
                  <button onClick={() => submit("dismissed")}
                    disabled={!reviewer || submitting}
                    className="bg-white border border-gray-300 text-gray-700 text-sm px-4 py-2 rounded hover:bg-gray-50 disabled:opacity-40">
                    ✗ Dismiss
                  </button>
                  <input value={dismissReason} onChange={e => setDismissReason(e.target.value)}
                    placeholder="Dismiss reason (optional)"
                    className="flex-1 border border-gray-200 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
