"""
Commitment Handoff Report generator.
Auto-generated before implementation kickoff from all pre-signature sources.
Reviewed by Implementation Manager before first customer contact.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.commitment import Commitment, CommitmentStatus, CommitmentType
from models.capability import CapabilityMatch, CapabilityStatus
from models.conflict import Conflict, ConflictStatus


async def generate_handoff_report(db: AsyncSession, workspace_id: str, account_id: str) -> dict:
    """Generate a structured commitment handoff report for an account."""
    result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == workspace_id,
            Commitment.account_id == account_id,
            Commitment.status.notin_([CommitmentStatus.fulfilled, CommitmentStatus.missed]),
        ).order_by(Commitment.severity_tier, Commitment.due_date.asc().nullslast())
    )
    commitments = result.scalars().all()

    # Categorise for IM review
    unowned, date_infeasible, legal_pending, unsupported_cap, normal = [], [], [], [], []

    for c in commitments:
        flags = []
        if not c.responsible_owner:
            flags.append("unowned")
        if c.legal_review_status.value == "pending":
            flags.append("legal_pending")

        # Check capability match
        cap_result = await db.execute(
            select(CapabilityMatch).where(CapabilityMatch.commitment_id == c.id)
            .order_by(CapabilityMatch.created_at.desc()).limit(1)
        )
        cap = cap_result.scalar_one_or_none()

        # Check conflicts
        conflict_result = await db.execute(
            select(Conflict).where(
                Conflict.commitment_a_id == c.id,
                Conflict.status == ConflictStatus.open,
            ).limit(1)
        )
        has_conflict = conflict_result.scalar_one_or_none() is not None

        item = {
            "id": str(c.id),
            "statement": c.statement,
            "evidence_passage": c.evidence_passage,
            "type": c.commitment_type.value,
            "severity": c.severity_tier.value,
            "owner": c.responsible_owner,
            "due_date": str(c.due_date) if c.due_date else None,
            "due_date_confidence": c.due_date_confidence.value,
            "capability_status": cap.match_status.value if cap else "unknown",
            "has_open_conflict": has_conflict,
            "flags": flags,
        }

        if "unowned" in flags:
            unowned.append(item)
        elif "legal_pending" in flags:
            legal_pending.append(item)
        elif cap and cap.match_status in (CapabilityStatus.unsupported,):
            unsupported_cap.append(item)
        else:
            normal.append(item)

    return {
        "account_id": account_id,
        "workspace_id": workspace_id,
        "total_commitments": len(commitments),
        "summary": {
            "unowned": len(unowned),
            "pending_legal_review": len(legal_pending),
            "unsupported_capability": len(unsupported_cap),
            "normal": len(normal),
        },
        "risk_items": {
            "unowned": unowned,
            "pending_legal_review": legal_pending,
            "unsupported_capability": unsupported_cap,
        },
        "standard_commitments": normal,
        "note": (
            "Review all items before the implementation kickoff call. "
            "Flag any unowned or unsupported items with the account team before customer contact."
        ),
    }
