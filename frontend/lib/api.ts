const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export type SeverityTier = "critical" | "high" | "medium" | "low";
export type CommitmentType = "feature" | "date" | "pricing" | "security_compliance" | "performance" | "sla" | "custom" | "other";
export type CommitmentStatus = "proposed" | "confirmed" | "in_progress" | "at_risk" | "fulfilled" | "disputed" | "missed";
export type CandidateVerdict = "pending" | "confirmed" | "edited" | "dismissed";
export type LegalReviewStatus = "not_required" | "pending" | "approved" | "rejected" | "escalated";
export type ConflictType = "cross_customer" | "cross_document" | "date_infeasible" | "capability_gap" | "self_contradiction";
export type CapabilityStatus = "current" | "on_roadmap" | "unsupported" | "unknown";

export interface Workspace {
  id: string; name: string; organisation: string; created_by: string;
  salesforce_org?: string; gong_workspace?: string; created_at: string;
}

export interface Source {
  id: string; workspace_id: string; account_id: string; account_name: string;
  source_type: string; title: string; uploaded_by: string;
  processed_at?: string; created_at: string;
}

export interface Candidate {
  id: string; source_id: string; workspace_id: string;
  raw_statement: string; evidence_passage: string; evidence_location?: string;
  commitment_type: CommitmentType; severity_tier: SeverityTier;
  promisor?: string; counterparty?: string; raw_due_date?: string;
  extraction_confidence: number; classification_reason?: string;
  verdict: CandidateVerdict; created_at: string;
}

export interface Commitment {
  id: string; workspace_id: string; statement: string;
  commitment_type: CommitmentType; severity_tier: SeverityTier;
  account_id: string; account_name: string; promisor?: string;
  responsible_owner?: string; due_date?: string; due_date_confidence: string;
  status: CommitmentStatus; arr_exposure?: number;
  legal_review_status: LegalReviewStatus; created_at: string;
}

export interface Capability {
  id: string; workspace_id: string; name: string; description: string;
  status: CapabilityStatus; roadmap_date?: string; owner_team?: string; created_at: string;
}

export interface Conflict {
  id: string; workspace_id: string; commitment_a_id: string;
  commitment_b_id?: string; conflict_type: ConflictType;
  description: string; status: string; detected_at: string;
}

export interface Alert {
  id: string; commitment_id: string; trigger_type: string;
  recipient_type: string; recipient: string; message: string;
  acknowledged_at?: string; created_at: string;
}

export interface LegalReview {
  id: string; commitment_id: string; reviewer?: string;
  status: LegalReviewStatus; notes?: string; reviewed_at?: string;
}

// ─── Workspaces ───────────────────────────────────────────────────────────────

export const api = {
  workspaces: {
    list: () => req<Workspace[]>("GET", "/workspaces/"),
    get: (id: string) => req<Workspace>("GET", `/workspaces/${id}`),
    create: (body: { name: string; organisation: string; created_by: string }) =>
      req<Workspace>("POST", "/workspaces/", body),
  },

  // ─── Sources ────────────────────────────────────────────────────────────────
  sources: {
    list: (workspaceId: string) => req<Source[]>("GET", `/workspaces/${workspaceId}/sources`),
    get: (id: string) => req<Source>("GET", `/sources/${id}`),
    ingest: (body: {
      workspace_id: string; account_id: string; account_name: string;
      source_type: string; title: string; uploaded_by: string; raw_text: string;
    }) => req<{ source: Source; candidates_created: number; message: string }>("POST", "/sources/ingest", body),
  },

  // ─── Candidates (AE review gate) ────────────────────────────────────────────
  candidates: {
    list: (workspaceId: string) => req<Candidate[]>("GET", `/workspaces/${workspaceId}/candidates`),
    review: (id: string, body: {
      verdict: "confirmed" | "edited" | "dismissed";
      reviewed_by: string; edited_statement?: string;
      dismiss_reason?: string; responsible_owner?: string; arr_exposure?: number;
    }) => req<{ candidate_id: string; verdict: string; commitment_id?: string; message: string }>(
      "POST", `/candidates/${id}/review`, body
    ),
  },

  // ─── Commitments ────────────────────────────────────────────────────────────
  commitments: {
    list: (workspaceId: string, params?: { status?: string; account_id?: string }) => {
      const q = new URLSearchParams(params as Record<string, string>).toString();
      return req<Commitment[]>("GET", `/workspaces/${workspaceId}/commitments${q ? `?${q}` : ""}`);
    },
    get: (id: string) => req<Commitment>("GET", `/commitments/${id}`),
    updateStatus: (id: string, body: { status: CommitmentStatus; actor: string; note?: string }) =>
      req<Commitment>("PATCH", `/commitments/${id}/status`, body),
    attachEvidence: (id: string, body: { attached_by: string; evidence_type: string; evidence_url?: string; evidence_text?: string }) =>
      req("POST", `/commitments/${id}/evidence`, body),
  },

  // ─── Capabilities ───────────────────────────────────────────────────────────
  capabilities: {
    list: (workspaceId: string) => req<Capability[]>("GET", `/workspaces/${workspaceId}/capabilities`),
    create: (workspaceId: string, body: { name: string; description: string; status?: CapabilityStatus; roadmap_date?: string }) =>
      req<Capability>("POST", `/workspaces/${workspaceId}/capabilities`, body),
  },

  // ─── Conflicts ──────────────────────────────────────────────────────────────
  conflicts: {
    list: (workspaceId: string, status = "open") =>
      req<Conflict[]>("GET", `/workspaces/${workspaceId}/conflicts?status=${status}`),
    resolve: (id: string, body: { resolved_by: string; resolution_notes?: string }) =>
      req<Conflict>("PATCH", `/conflicts/${id}/resolve`, body),
  },

  // ─── Legal ──────────────────────────────────────────────────────────────────
  legal: {
    queue: (workspaceId: string) => req<LegalReview[]>("GET", `/workspaces/${workspaceId}/legal-queue`),
    adjudicate: (id: string, body: { reviewer: string; decision: string; notes?: string }) =>
      req<LegalReview>("POST", `/legal-reviews/${id}/adjudicate`, body),
  },

  // ─── Alerts ─────────────────────────────────────────────────────────────────
  alerts: {
    list: (workspaceId: string, unacknowledgedOnly = false) =>
      req<Alert[]>("GET", `/workspaces/${workspaceId}/alerts${unacknowledgedOnly ? "?unacknowledged_only=true" : ""}`),
    acknowledge: (id: string, action_taken?: string) =>
      req("POST", `/alerts/${id}/acknowledge`, { action_taken }),
  },

  // ─── Reports ────────────────────────────────────────────────────────────────
  reports: {
    qbrView: (accountId: string, workspaceId: string) =>
      req<any>("GET", `/accounts/${accountId}/qbr-view?workspace_id=${workspaceId}`),
    history: (accountId: string, workspaceId: string) =>
      req<any>("GET", `/accounts/${accountId}/history?workspace_id=${workspaceId}`),
    handoff: (accountId: string, workspaceId: string) =>
      req<any>("GET", `/accounts/${accountId}/handoff-report?workspace_id=${workspaceId}`),
    portfolio: (workspaceId: string) =>
      req<any>("GET", `/workspaces/${workspaceId}/portfolio`),
    pmView: (workspaceId: string) =>
      req<any>("GET", `/workspaces/${workspaceId}/pm-view`),
  },
};
