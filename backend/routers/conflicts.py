from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from database import get_db
from models.conflict import Conflict, ConflictType, ConflictStatus

router = APIRouter(tags=["conflicts"])

class ConflictRead(BaseModel):
    id: UUID
    workspace_id: UUID
    commitment_a_id: UUID
    commitment_b_id: UUID | None
    conflict_type: ConflictType
    description: str
    status: ConflictStatus
    detected_at: datetime
    model_config = {"from_attributes": True}

class ResolveRequest(BaseModel):
    resolved_by: str
    resolution_notes: str | None = None
    status: ConflictStatus = ConflictStatus.resolved

@router.get("/workspaces/{workspace_id}/conflicts", response_model=list[ConflictRead])
async def list_conflicts(workspace_id: UUID, status: str = "open", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conflict).where(
            Conflict.workspace_id == workspace_id,
            Conflict.status == ConflictStatus(status),
        ).order_by(Conflict.detected_at.desc())
    )
    return result.scalars().all()

@router.patch("/conflicts/{conflict_id}/resolve", response_model=ConflictRead)
async def resolve_conflict(conflict_id: UUID, payload: ResolveRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conflict not found.")
    c.status = payload.status
    c.resolved_by = payload.resolved_by
    c.resolved_at = datetime.now(timezone.utc)
    c.resolution_notes = payload.resolution_notes
    return c
