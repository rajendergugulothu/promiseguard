from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from database import get_db
from models.source import Source, SourceType
from models.candidate import CommitmentCandidate
from services.extractor import extract_commitments

router = APIRouter(tags=["sources"])

class SourceIngest(BaseModel):
    workspace_id: UUID
    account_id: str
    account_name: str
    opportunity_id: str | None = None
    source_type: SourceType
    title: str
    source_date: date | None = None
    uploaded_by: str
    raw_text: str

class SourceRead(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: str
    account_name: str
    source_type: SourceType
    title: str
    uploaded_by: str
    processed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}

class IngestResponse(BaseModel):
    source: SourceRead
    candidates_created: int
    message: str

@router.post("/sources/ingest", response_model=IngestResponse, status_code=201)
async def ingest_source(payload: SourceIngest, db: AsyncSession = Depends(get_db)):
    """Ingest a document or transcript and extract commitment candidates."""
    source = Source(
        workspace_id=payload.workspace_id,
        account_id=payload.account_id,
        account_name=payload.account_name,
        opportunity_id=payload.opportunity_id,
        source_type=payload.source_type,
        title=payload.title,
        source_date=payload.source_date,
        uploaded_by=payload.uploaded_by,
        raw_text=payload.raw_text,
    )
    db.add(source)
    await db.flush()

    candidates = await extract_commitments(db, str(source.id))

    return IngestResponse(
        source=source,
        candidates_created=len(candidates),
        message=f"Extracted {len(candidates)} commitment candidate(s). Pending AE review.",
    )

@router.get("/workspaces/{workspace_id}/sources", response_model=list[SourceRead])
async def list_sources(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.workspace_id == workspace_id).order_by(Source.created_at.desc())
    )
    return result.scalars().all()

@router.get("/sources/{source_id}", response_model=SourceRead)
async def get_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Source not found.")
    return s
