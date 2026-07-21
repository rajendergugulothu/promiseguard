"""
AE Review Gate — the most critical router in PromiseGuard.

POST /candidates/{id}/review is the only code path that creates Commitment records.
AE must see all candidates first. No candidate with verdict='pending' can have a commitment_id.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timezone
from typing import Literal

from database import get_db
from models.candidate import CommitmentCandidate, CandidateVerdict, CommitmentType, SeverityTier
from models.commitment import Commitment, CommitmentStatus, LegalReviewStatus, DateConfidence
from models.legal import LegalReview
from models.audit import AuditLog
from models.source import Source
from services.date_normalizer import normalize_date
from services.capability_matcher import match_capability
from services.conflict_detector import detect_conflicts
from services.risk_scorer import compute_risk

router = APIRouter(tags=["candidates"])

class CandidateRead(BaseModel):
    id: UUID
    source_id: UUID
    workspace_id: UUID
    raw_statement: str
    evidence_passage: str
    evidence_location: str | None
    commitment_type: CommitmentType
    severity_tier: SeverityTier
    promisor: str | None
    counterparty: str | None
    raw_due_date: str | None
    extraction_confidence: float
    classification_reason: str | None
    verdict: CandidateVerdict
    created_at: datetime
    model_config = {"from_attributes": True}

class ReviewRequest(BaseModel):
    verdict: Literal["confirmed", "edited", "dismissed"]
    reviewed_by: str = Field(..., example="jordan.marsh@scaleops.com")
    edited_statement: str | None = None
    dismiss_reason: str | None = None
    responsible_owner: str | None = None
    arr_exposure: float | None = None

class ReviewResponse(BaseModel):
    candidate_id: UUID
    verdict: str
    commitment_id: UUID | None = None
    message: str

@router.get("/workspaces/{workspace_id}/candidates", response_model=list[CandidateRead])
async def list_pending_candidates(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """AE review queue — pending candidates only."""
    result = await db.execute(
        select(CommitmentCandidate).where(
            CommitmentCandidate.workspace_id == workspace_id,
            CommitmentCandidate.verdict == CandidateVerdict.pending,
        ).order_by(CommitmentCandidate.created_at)
    )
    return result.scalars().all()

@router.post("/candidates/{candidate_id}/review", response_model=ReviewResponse)
async def review_candidate(
    candidate_id: UUID,
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    AE review gate. The ONLY code path that creates Commitment records.

    confirmed | edited → creates Commitment, updates candidate.commitment_id
    dismissed          → archives candidate, no Commitment created
    """
    result = await db.execute(select(CommitmentCandidate).where(CommitmentCandidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    if candidate.verdict != CandidateVerdict.pending:
        raise HTTPException(status_code=409, detail=f"Candidate already reviewed: {candidate.verdict.value}")

    now = datetime.now(timezone.utc)
    candidate.reviewed_by = payload.reviewed_by
    candidate.reviewed_at = now
    candidate.verdict = CandidateVerdict(payload.verdict)

    if payload.verdict == "dismissed":
        candidate.dismiss_reason = payload.dismiss_reason
        db.add(AuditLog(
            workspace_id=candidate.workspace_id,
            entity_type="candidate",
            entity_id=candidate.id,
            action="candidate_dismissed",
            actor=payload.reviewed_by,
            new_value={"reason": payload.dismiss_reason},
        ))
        await db.commit()
        return ReviewResponse(candidate_id=candidate_id, verdict="dismissed",
                              message="Candidate dismissed. Not entered into the commitment ledger.")

    # Confirmed or edited — create Commitment
    statement = payload.edited_statement if payload.edited_statement else candidate.raw_statement
    if payload.edited_statement:
        candidate.edited_statement = payload.edited_statement

    # Normalise due date
    due_date, due_conf = await normalize_date(candidate.raw_due_date)

    # Determine legal gate
    is_legal_tier = candidate.commitment_type.value == "security_compliance"
    legal_status = LegalReviewStatus.pending if is_legal_tier else LegalReviewStatus.not_required

    commitment = Commitment(
        workspace_id=candidate.workspace_id,
        source_id=candidate.source_id,
        candidate_id=candidate.id,
        statement=statement,
        evidence_passage=candidate.evidence_passage,
        evidence_location=candidate.evidence_location,
        commitment_type=candidate.commitment_type,
        severity_tier=candidate.severity_tier,
        account_id="",          # populated from source metadata in production
        account_name="",        # populated from source metadata in production
        promisor=candidate.promisor,
        responsible_owner=payload.responsible_owner,
        customer_contact=candidate.counterparty,
        due_date=due_date,
        due_date_confidence=due_conf,
        raw_due_date_text=candidate.raw_due_date,
        status=CommitmentStatus.proposed,
        arr_exposure=payload.arr_exposure,
        legal_review_status=legal_status,
    )

    # Populate account from source
    src_result = await db.execute(
        select(Source).where(Source.id == candidate.source_id)
    )
    src = src_result.scalar_one_or_none()
    if src:
        commitment.account_id = src.account_id
        commitment.account_name = src.account_name

    db.add(commitment)
    await db.flush()

    # Update candidate to link to commitment
    candidate.commitment_id = commitment.id

    # Create legal review record if needed
    if is_legal_tier:
        lr = LegalReview(commitment_id=commitment.id)
        db.add(lr)

    # Run capability matching, conflict detection, risk scoring
    try:
        await match_capability(db, str(commitment.id))
    except Exception:
        pass  # Capability matching is best-effort; commitment is created regardless

    try:
        await detect_conflicts(db, str(commitment.id))
    except Exception:
        pass

    try:
        await compute_risk(db, str(commitment.id))
    except Exception:
        pass

    db.add(AuditLog(
        workspace_id=candidate.workspace_id,
        entity_type="commitment",
        entity_id=commitment.id,
        action="commitment_created",
        actor=payload.reviewed_by,
        new_value={"statement": statement[:100], "type": candidate.commitment_type.value},
    ))
    await db.commit()

    legal_note = " Routed to legal review queue." if is_legal_tier else ""
    return ReviewResponse(
        candidate_id=candidate_id,
        verdict=payload.verdict,
        commitment_id=commitment.id,
        message=f"Commitment created and entered into the ledger.{legal_note}",
    )
