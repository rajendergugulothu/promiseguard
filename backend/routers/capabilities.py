from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from database import get_db
from models.capability import CapabilityRegistry, CapabilityStatus
from services.capability_matcher import embed_text

router = APIRouter(tags=["capabilities"])

class CapabilityCreate(BaseModel):
    name: str
    description: str
    status: CapabilityStatus = CapabilityStatus.unknown
    roadmap_date: date | None = None
    roadmap_confidence: str | None = None
    owner_team: str | None = None

class CapabilityRead(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str
    status: CapabilityStatus
    roadmap_date: date | None
    roadmap_confidence: str | None
    owner_team: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

@router.post("/workspaces/{workspace_id}/capabilities", response_model=CapabilityRead, status_code=201)
async def create_capability(workspace_id: UUID, payload: CapabilityCreate, db: AsyncSession = Depends(get_db)):
    embedding = await embed_text(f"{payload.name}: {payload.description}")
    cap = CapabilityRegistry(
        workspace_id=workspace_id,
        embedding=embedding,
        **payload.model_dump(),
    )
    db.add(cap)
    await db.flush()
    return cap

@router.get("/workspaces/{workspace_id}/capabilities", response_model=list[CapabilityRead])
async def list_capabilities(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CapabilityRegistry).where(CapabilityRegistry.workspace_id == workspace_id)
    )
    return result.scalars().all()

@router.patch("/capabilities/{capability_id}", response_model=CapabilityRead)
async def update_capability(capability_id: UUID, payload: CapabilityCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CapabilityRegistry).where(CapabilityRegistry.id == capability_id))
    cap = result.scalar_one_or_none()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found.")
    for k, v in payload.model_dump().items():
        setattr(cap, k, v)
    cap.embedding = await embed_text(f"{payload.name}: {payload.description}")
    return cap
