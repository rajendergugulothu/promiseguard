"""
Conflict detector — four conflict types.
Runs after every commitment is confirmed.
"""

import os
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic import AsyncAnthropic

from models.commitment import Commitment, CommitmentStatus
from models.capability import CapabilityMatch, CapabilityStatus
from models.conflict import Conflict, ConflictType, ConflictStatus
from models.audit import AuditLog

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


async def detect_conflicts(db: AsyncSession, commitment_id: str) -> list[Conflict]:
    """Run all four conflict detection checks for a newly confirmed commitment."""
    result = await db.execute(select(Commitment).where(Commitment.id == UUID(commitment_id)))
    commitment = result.scalar_one_or_none()
    if not commitment:
        raise ValueError(f"Commitment {commitment_id} not found.")

    conflicts = []

    # Check 1: Date infeasibility (deterministic)
    cap_result = await db.execute(
        select(CapabilityMatch).where(CapabilityMatch.commitment_id == commitment.id)
    )
    cap_match = cap_result.scalar_one_or_none()
    if (cap_match and cap_match.roadmap_date and commitment.due_date
            and cap_match.roadmap_date > commitment.due_date):
        c = Conflict(
            workspace_id=commitment.workspace_id,
            commitment_a_id=commitment.id,
            conflict_type=ConflictType.date_infeasible,
            description=(
                f"Commitment due {commitment.due_date} but capability "
                f"not ready until {cap_match.roadmap_date}."
            ),
        )
        db.add(c)
        conflicts.append(c)

    # Check 2: Capability gap (deterministic)
    if cap_match and cap_match.match_status == CapabilityStatus.unsupported:
        c = Conflict(
            workspace_id=commitment.workspace_id,
            commitment_a_id=commitment.id,
            conflict_type=ConflictType.capability_gap,
            description=f"Commitment requires a capability classified as unsupported.",
        )
        db.add(c)
        conflicts.append(c)

    # Check 3: Cross-customer (same commitment, different terms, different account)
    similar_result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == commitment.workspace_id,
            Commitment.id != commitment.id,
            Commitment.commitment_type == commitment.commitment_type,
            Commitment.account_id != commitment.account_id,
            Commitment.status.notin_([CommitmentStatus.fulfilled, CommitmentStatus.missed]),
        ).limit(10)
    )
    similar = similar_result.scalars().all()
    for other in similar:
        if await _statements_conflict(commitment.statement, other.statement):
            c = Conflict(
                workspace_id=commitment.workspace_id,
                commitment_a_id=commitment.id,
                commitment_b_id=other.id,
                conflict_type=ConflictType.cross_customer,
                description=(
                    f"Similar commitment made with different terms to "
                    f"{other.account_name} ({other.account_id})."
                ),
            )
            db.add(c)
            conflicts.append(c)
            break  # one conflict per check is sufficient signal

    # Check 4: Self-contradiction within same account
    account_result = await db.execute(
        select(Commitment).where(
            Commitment.workspace_id == commitment.workspace_id,
            Commitment.account_id == commitment.account_id,
            Commitment.id != commitment.id,
            Commitment.status.notin_([CommitmentStatus.fulfilled, CommitmentStatus.missed]),
        ).limit(20)
    )
    account_commitments = account_result.scalars().all()
    for other in account_commitments:
        if await _statements_contradict(commitment.statement, other.statement):
            c = Conflict(
                workspace_id=commitment.workspace_id,
                commitment_a_id=commitment.id,
                commitment_b_id=other.id,
                conflict_type=ConflictType.self_contradiction,
                description=f"Commitment may contradict another commitment for {commitment.account_name}.",
            )
            db.add(c)
            conflicts.append(c)
            break

    if conflicts:
        await db.flush()
        for c in conflicts:
            db.add(AuditLog(
                workspace_id=commitment.workspace_id,
                entity_type="conflict",
                entity_id=c.id,
                action="conflict_detected",
                actor="system",
                new_value={"type": c.conflict_type.value},
            ))

    return conflicts


async def _statements_conflict(a: str, b: str) -> bool:
    """Check if two commitment statements conflict (different terms, same subject)."""
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{"role": "user", "content": (
            f"Do these two commitments conflict (same subject, different terms)? "
            f"Answer only YES or NO.\n\nA: {a}\nB: {b}"
        )}],
    )
    return "YES" in message.content[0].text.upper()


async def _statements_contradict(a: str, b: str) -> bool:
    """Check if two commitments within the same account contradict each other."""
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{"role": "user", "content": (
            f"Do these two commitments made to the same customer contradict each other? "
            f"Answer only YES or NO.\n\nA: {a}\nB: {b}"
        )}],
    )
    return "YES" in message.content[0].text.upper()
