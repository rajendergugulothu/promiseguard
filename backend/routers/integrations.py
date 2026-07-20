from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from database import get_db
from services.gong_service import pull_recent_transcripts

router = APIRouter(tags=["integrations"])


class GongPullRequest(BaseModel):
    workspace_id: UUID
    account_id: str
    account_name: str
    days_back: int = 30


@router.post("/integrations/gong/pull")
async def pull_gong_transcripts(payload: GongPullRequest, db: AsyncSession = Depends(get_db)):
    """Pull recent Gong transcripts for an account and extract commitment candidates."""
    try:
        sources = await pull_recent_transcripts(
            db,
            workspace_id=str(payload.workspace_id),
            account_id=payload.account_id,
            account_name=payload.account_name,
            days_back=payload.days_back,
        )
        return {
            "sources_created": len(sources),
            "message": f"Pulled {len(sources)} transcript(s) from Gong. Commitment extraction running.",
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
