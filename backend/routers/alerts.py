from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from database import get_db
from models.risk import Alert, AlertTrigger, AlertRecipientType

router = APIRouter(tags=["alerts"])

class AlertRead(BaseModel):
    id: UUID
    commitment_id: UUID
    trigger_type: AlertTrigger
    recipient_type: AlertRecipientType
    recipient: str
    message: str
    acknowledged_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}

class AcknowledgeRequest(BaseModel):
    action_taken: str | None = None

@router.get("/workspaces/{workspace_id}/alerts", response_model=list[AlertRead])
async def list_alerts(workspace_id: UUID, unacknowledged_only: bool = False, db: AsyncSession = Depends(get_db)):
    q = select(Alert).where(Alert.workspace_id == workspace_id)
    if unacknowledged_only:
        q = q.where(Alert.acknowledged_at.is_(None))
    result = await db.execute(q.order_by(Alert.created_at.desc()))
    return result.scalars().all()

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: UUID, payload: AcknowledgeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.action_taken = payload.action_taken
    return {"acknowledged": True}
