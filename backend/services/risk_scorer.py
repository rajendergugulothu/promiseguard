"""
Risk scorer — deterministic composite formula.
Re-runs on every state change as a background task.

risk_score = severity_weight × urgency × (1 - feasibility) × arr_exposure_factor

Capped at 1.0.
"""

from datetime import date, datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.commitment import Commitment, CommitmentStatus
from models.capability import CapabilityMatch, CapabilityStatus
from models.conflict import Conflict, ConflictStatus
from models.risk import RiskScore

SEVERITY_WEIGHTS = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
FEASIBILITY_BY_STATUS = {"current": 0.95, "on_roadmap": 0.6, "unknown": 0.4, "unsupported": 0.05}
MEDIAN_ARR = 500_000.0  # placeholder — update from real workspace data


def _urgency(due_date: date | None) -> float:
    if not due_date:
        return 0.4  # unknown due date → moderate urgency
    days = (due_date - date.today()).days
    if days < 0:
        return 1.0  # overdue
    if days < 30:
        return 1.0
    if days < 90:
        return 0.7
    return 0.4


def _feasibility(match_status: CapabilityStatus | None) -> float:
    if match_status is None:
        return 0.4  # no match → unknown feasibility
    return FEASIBILITY_BY_STATUS.get(match_status.value, 0.4)


async def compute_risk(db: AsyncSession, commitment_id: str) -> RiskScore:
    """Compute and store risk score for a commitment."""
    result = await db.execute(select(Commitment).where(Commitment.id == UUID(commitment_id)))
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise ValueError(f"Commitment {commitment_id} not found.")

    # Get latest capability match
    cap_result = await db.execute(
        select(CapabilityMatch)
        .where(CapabilityMatch.commitment_id == commitment.id)
        .order_by(CapabilityMatch.created_at.desc())
        .limit(1)
    )
    cap_match = cap_result.scalar_one_or_none()

    # Count open conflicts
    conflict_count_result = await db.execute(
        select(func.count()).select_from(Conflict).where(
            Conflict.commitment_a_id == commitment.id,
            Conflict.status == ConflictStatus.open,
        )
    )
    open_conflicts = conflict_count_result.scalar() or 0

    sev_weight = SEVERITY_WEIGHTS.get(commitment.severity_tier.value, 0.5)
    urgency = _urgency(commitment.due_date)
    feas = _feasibility(cap_match.match_status if cap_match else None)
    # Use 1.0 as neutral factor when ARR is unknown — avoids zeroing out otherwise
    # high-risk commitments just because arr_exposure hasn't been set yet.
    arr_raw = float(commitment.arr_exposure) if commitment.arr_exposure else None
    arr_factor = min(arr_raw / MEDIAN_ARR, 2.0) if arr_raw is not None else 1.0

    score = sev_weight * urgency * (1 - feas) * arr_factor
    score = min(round(score, 3), 1.0)

    rs = RiskScore(
        commitment_id=commitment.id,
        score=score,
        severity_weight=sev_weight,
        urgency_factor=urgency,
        feasibility_factor=feas,
        arr_exposure_factor=arr_factor,
        open_conflicts_count=open_conflicts,
    )
    db.add(rs)
    return rs
