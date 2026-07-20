"""
Five reporting views:
1. QBR prep view — per account, for CSM
2. Portfolio risk dashboard — all accounts, for CCO
3. Account history view — full ledger including closed, for CS Ops
4. Commitment handoff report — pre-kickoff, for IM
5. PM portfolio view — recurring promises and product gaps, for PM
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime

from database import get_db
from models.commitment import Commitment, CommitmentStatus, CommitmentType
from models.candidate import SeverityTier
from models.risk import RiskScore
from models.conflict import Conflict, ConflictStatus
from services.handoff_report import generate_handoff_report

router = APIRouter(tags=["reports"])


@router.get("/accounts/{account_id}/qbr-view")
async def qbr_prep_view(account_id: str, workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """CSM view — all outstanding commitments for an account before a QBR."""
    result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == workspace_id,
            Commitment.account_id == account_id,
            Commitment.status.notin_([CommitmentStatus.fulfilled, CommitmentStatus.missed]),
        ).order_by(Commitment.severity_tier, Commitment.due_date.asc().nullslast())
    )
    commitments = result.scalars().all()

    items = []
    for c in commitments:
        rs_result = await db.execute(
            select(RiskScore).where(RiskScore.commitment_id == c.id)
            .order_by(RiskScore.computed_at.desc()).limit(1)
        )
        rs = rs_result.scalar_one_or_none()
        conflict_result = await db.execute(
            select(func.count()).select_from(Conflict).where(
                Conflict.commitment_a_id == c.id, Conflict.status == ConflictStatus.open
            )
        )
        open_conflicts = conflict_result.scalar() or 0

        items.append({
            "id": str(c.id),
            "statement": c.statement,
            "type": c.commitment_type.value,
            "severity": c.severity_tier.value,
            "owner": c.responsible_owner,
            "due_date": str(c.due_date) if c.due_date else None,
            "status": c.status.value,
            "risk_score": round(rs.score, 2) if rs else None,
            "open_conflicts": open_conflicts,
            "legal_status": c.legal_review_status.value,
        })

    return {
        "account_id": account_id,
        "total": len(items),
        "overdue": sum(1 for i in items if i["due_date"] and i["due_date"] < str(date.today())),
        "unowned": sum(1 for i in items if not i["owner"]),
        "with_open_conflicts": sum(1 for i in items if i["open_conflicts"] > 0),
        "commitments": items,
    }


@router.get("/accounts/{account_id}/history")
async def account_history(account_id: str, workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """CS Ops view — full commitment history including fulfilled and missed. Survives CSM reassignment."""
    result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == workspace_id,
            Commitment.account_id == account_id,
        ).order_by(Commitment.created_at.desc())
    )
    commitments = result.scalars().all()
    return {
        "account_id": account_id,
        "total": len(commitments),
        "commitments": [
            {
                "id": str(c.id),
                "statement": c.statement,
                "type": c.commitment_type.value,
                "severity": c.severity_tier.value,
                "status": c.status.value,
                "owner": c.responsible_owner,
                "due_date": str(c.due_date) if c.due_date else None,
                "fulfilled_at": str(c.fulfilled_at) if c.fulfilled_at else None,
                "evidence_passage": c.evidence_passage,
            }
            for c in commitments
        ],
    }


@router.get("/accounts/{account_id}/handoff-report")
async def handoff_report(account_id: str, workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """IM view — commitment handoff report generated before kickoff."""
    return await generate_handoff_report(db, str(workspace_id), account_id)


@router.get("/workspaces/{workspace_id}/portfolio")
async def portfolio_dashboard(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """CCO view — commitment risk across all accounts with ARR exposure."""
    result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == workspace_id,
            Commitment.status.notin_([CommitmentStatus.fulfilled, CommitmentStatus.missed]),
        )
    )
    all_commitments = result.scalars().all()

    by_account: dict[str, dict] = {}
    for c in all_commitments:
        if c.account_id not in by_account:
            by_account[c.account_id] = {
                "account_id": c.account_id,
                "account_name": c.account_name,
                "total_commitments": 0,
                "unowned": 0,
                "critical_count": 0,
                "total_arr_exposure": 0.0,
            }
        by_account[c.account_id]["total_commitments"] += 1
        if not c.responsible_owner:
            by_account[c.account_id]["unowned"] += 1
        if c.severity_tier == SeverityTier.critical:
            by_account[c.account_id]["critical_count"] += 1
        by_account[c.account_id]["total_arr_exposure"] += float(c.arr_exposure or 0)

    total_arr = sum(v["total_arr_exposure"] for v in by_account.values())
    return {
        "workspace_id": str(workspace_id),
        "total_open_commitments": len(all_commitments),
        "accounts_at_risk": len(by_account),
        "total_arr_exposure": round(total_arr, 2),
        "accounts": sorted(by_account.values(), key=lambda x: x["total_arr_exposure"], reverse=True),
    }


@router.get("/workspaces/{workspace_id}/pm-view")
async def pm_portfolio_view(workspace_id: UUID, db: AsyncSession = Depends(get_db)):
    """PM view — recurring promise patterns and product gaps."""
    result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == workspace_id,
            Commitment.commitment_type == CommitmentType.feature,
        )
    )
    feature_commitments = result.scalars().all()

    # Group by normalised statement (simple: first 60 chars as key)
    patterns: dict[str, dict] = {}
    for c in feature_commitments:
        key = c.statement[:60].lower().strip()
        if key not in patterns:
            patterns[key] = {"statement": c.statement, "count": 0, "accounts": [], "total_arr": 0.0}
        patterns[key]["count"] += 1
        if c.account_name not in patterns[key]["accounts"]:
            patterns[key]["accounts"].append(c.account_name)
        patterns[key]["total_arr"] += float(c.arr_exposure or 0)

    recurring = [p for p in patterns.values() if p["count"] >= 2]
    recurring.sort(key=lambda x: x["total_arr"], reverse=True)

    return {
        "workspace_id": str(workspace_id),
        "total_feature_commitments": len(feature_commitments),
        "recurring_patterns": len(recurring),
        "patterns": recurring,
        "note": "Patterns are grouped by first 60 characters of commitment statement. Review manually for semantic grouping.",
    }
