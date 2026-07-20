"""
Alert generation + routing.
8 trigger types, 4 recipient types.
"""

from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.commitment import Commitment, CommitmentType
from models.risk import Alert, AlertTrigger, AlertRecipientType
from models.audit import AuditLog

HIGH_RISK_THRESHOLD = 0.7


async def generate_alerts(db: AsyncSession, commitment_id: str, latest_risk_score: float) -> list[Alert]:
    """Generate alerts for a commitment based on current state and risk score."""
    result = await db.execute(select(Commitment).where(Commitment.id == commitment_id))
    commitment = result.scalar_one_or_none()
    if not commitment:
        return []

    alerts = []
    today = date.today()

    # Deadline alerts
    if commitment.due_date:
        days = (commitment.due_date - today).days
        if 0 <= days <= 1:
            alerts.append(_make_alert(commitment, AlertTrigger.deadline_1d,
                f"Commitment due in {days} day(s): {commitment.statement[:100]}"))
        elif 2 <= days <= 7:
            alerts.append(_make_alert(commitment, AlertTrigger.deadline_7d,
                f"Commitment due in {days} days: {commitment.statement[:100]}"))
        elif 8 <= days <= 30:
            alerts.append(_make_alert(commitment, AlertTrigger.deadline_30d,
                f"Commitment due in {days} days: {commitment.statement[:100]}"))
        elif days < 0:
            alerts.append(_make_alert(commitment, AlertTrigger.commitment_missed,
                f"Commitment overdue by {abs(days)} days: {commitment.statement[:100]}"))

    # High risk unowned
    if latest_risk_score >= HIGH_RISK_THRESHOLD and not commitment.responsible_owner:
        alerts.append(_make_alert(commitment, AlertTrigger.high_risk_unowned,
            f"High-risk commitment has no owner: {commitment.statement[:100]}"))

    for alert in alerts:
        db.add(alert)
        # Route security/compliance to legal reviewer additionally
        if commitment.commitment_type == CommitmentType.security_compliance:
            legal_alert = Alert(
                workspace_id=commitment.workspace_id,
                commitment_id=commitment.id,
                trigger_type=alert.trigger_type,
                recipient_type=AlertRecipientType.legal_reviewer,
                recipient="legal-team",
                message=f"[LEGAL] {alert.message}",
            )
            db.add(legal_alert)
            alerts.append(legal_alert)

    if alerts:
        await db.flush()
        db.add(AuditLog(
            workspace_id=commitment.workspace_id,
            entity_type="commitment",
            entity_id=commitment.id,
            action="alerts_generated",
            actor="system",
            new_value={"alert_count": len(alerts)},
        ))

    return alerts


def _make_alert(commitment: Commitment, trigger: AlertTrigger, message: str) -> Alert:
    return Alert(
        workspace_id=commitment.workspace_id,
        commitment_id=commitment.id,
        trigger_type=trigger,
        recipient_type=AlertRecipientType.owner if commitment.responsible_owner else AlertRecipientType.account_csm,
        recipient=commitment.responsible_owner or "unassigned",
        message=message,
    )
