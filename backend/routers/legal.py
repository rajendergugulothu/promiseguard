from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from typing import Literal
from database import get_db
from models.legal import LegalReview
from models.commitment import Commitment, LegalReviewStatus
from models.audit import AuditLog

router = APIRouter(tags=["legal"])

class LegalReviewRead(BaseModel):
    id: UUID
    commitment_id: UUID
    reviewer: str | None
    status: LegalReviewStatus
    notes: str | None
    reviewed_at: datetime | None
    model_config = {"from_attributes": True}

class AdjudicateRequest(BaseModel):
    reviewer: str
    decision: Literal["approved", "rejected", "escalated"]
    notes: str | None = None
    escalated_to: str | None = None

@router.get("/workspaces/{workspace_id}/legal-queue", response_model=list[LegalReviewRead])
async def list_legal_queue(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LegalReview)
        .join(Commitment, LegalReview.commitment_id == Commitment.id)
        .where(Commitment.workspace_id == workspace_id, LegalReview.status == LegalReviewStatus.pending)
        .order_by(LegalReview.created_at)
    )
    return result.scalars().all()

@router.post("/legal-reviews/{review_id}/adjudicate", response_model=LegalReviewRead)
async def adjudicate(review_id: UUID, payload: AdjudicateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalReview).where(LegalReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Legal review not found.")

    review.reviewer = payload.reviewer
    review.status = LegalReviewStatus(payload.decision)
    review.notes = payload.notes
    review.reviewed_at = datetime.now(timezone.utc)
    review.escalated_to = payload.escalated_to

    # Update commitment legal_review_status
    comm_result = await db.execute(select(Commitment).where(Commitment.id == review.commitment_id))
    commitment = comm_result.scalar_one()
    commitment.legal_review_status = LegalReviewStatus(payload.decision)

    comm_ws = commitment.workspace_id
    db.add(AuditLog(
        workspace_id=comm_ws,
        entity_type="legal_review",
        entity_id=review.id,
        action="legal_adjudication",
        actor=payload.reviewer,
        new_value={"decision": payload.decision},
    ))
    return review
