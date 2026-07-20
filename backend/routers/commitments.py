from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date, timezone
from typing import Literal

from database import get_db
from models.commitment import Commitment, CommitmentStatus, CommitmentType, LegalReviewStatus, DateConfidence
from models.candidate import SeverityTier
from models.fulfillment import FulfillmentEvidence
from models.audit import AuditLog
from services.risk_scorer import compute_risk

router = APIRouter(tags=["commitments"])

class CommitmentRead(BaseModel):
    id: UUID
    workspace_id: UUID
    statement: str
    commitment_type: CommitmentType
    severity_tier: SeverityTier
    account_id: str
    account_name: str
    promisor: str | None
    responsible_owner: str | None
    due_date: date | None
    due_date_confidence: DateConfidence
    status: CommitmentStatus
    arr_exposure: float | None
    legal_review_status: LegalReviewStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class StatusUpdate(BaseModel):
    status: CommitmentStatus
    actor: str
    note: str | None = None

class EvidenceAttach(BaseModel):
    attached_by: str
    evidence_type: Literal["link", "document", "note"]
    evidence_url: str | None = None
    evidence_text: str | None = None

@router.get("/workspaces/{workspace_id}/commitments", response_model=list[CommitmentRead])
async def list_commitments(
    workspace_id: UUID,
    status: str | None = None,
    account_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Commitment).where(Commitment.workspace_id == workspace_id)
    if status:
        q = q.where(Commitment.status == CommitmentStatus(status))
    if account_id:
        q = q.where(Commitment.account_id == account_id)
    result = await db.execute(q.order_by(Commitment.created_at.desc()))
    return result.scalars().all()

@router.get("/commitments/{commitment_id}", response_model=CommitmentRead)
async def get_commitment(commitment_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Commitment).where(Commitment.id == commitment_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    return c

@router.patch("/commitments/{commitment_id}/status", response_model=CommitmentRead)
async def update_status(commitment_id: UUID, payload: StatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Commitment).where(Commitment.id == commitment_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found.")
    old_status = c.status
    c.status = payload.status
    c.status_updated_at = datetime.now(timezone.utc)
    c.status_note = payload.note

    if payload.status == CommitmentStatus.fulfilled:
        c.fulfilled_at = datetime.now(timezone.utc)
        c.fulfilled_by = payload.actor

    # Recompute risk on status change
    await compute_risk(db, str(c.id))

    db.add(AuditLog(
        workspace_id=c.workspace_id,
        entity_type="commitment",
        entity_id=c.id,
        action="status_changed",
        actor=payload.actor,
        old_value={"status": old_status.value},
        new_value={"status": payload.status.value},
    ))
    return c

@router.post("/commitments/{commitment_id}/evidence", status_code=201)
async def attach_evidence(commitment_id: UUID, payload: EvidenceAttach, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Commitment).where(Commitment.id == commitment_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found.")

    ev = FulfillmentEvidence(
        commitment_id=c.id,
        attached_by=payload.attached_by,
        evidence_type=payload.evidence_type,
        evidence_url=payload.evidence_url,
        evidence_text=payload.evidence_text,
    )
    db.add(ev)
    c.status = CommitmentStatus.fulfilled
    c.fulfilled_at = datetime.now(timezone.utc)
    c.fulfilled_by = payload.attached_by
    return {"message": "Evidence attached. Commitment marked as fulfilled.", "commitment_id": str(c.id)}
