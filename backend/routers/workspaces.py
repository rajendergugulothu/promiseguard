from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from database import get_db
from models.workspace import Workspace

router = APIRouter(tags=["workspaces"])

class WorkspaceCreate(BaseModel):
    name: str
    organisation: str
    created_by: str
    salesforce_org: str | None = None
    gong_workspace: str | None = None
    slack_team_id: str | None = None

class WorkspaceRead(BaseModel):
    id: UUID
    name: str
    organisation: str
    created_by: str
    salesforce_org: str | None
    gong_workspace: str | None
    slack_team_id: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

@router.post("/workspaces/", response_model=WorkspaceRead, status_code=201)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    ws = Workspace(**payload.model_dump())
    db.add(ws)
    await db.flush()
    return ws

@router.get("/workspaces/", response_model=list[WorkspaceRead])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return result.scalars().all()

@router.get("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws
