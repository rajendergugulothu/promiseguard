"""
CommitmentCandidate — raw LLM extraction, pre-AE review.

CRITICAL: verdict defaults to 'pending'.
A candidate with verdict='pending' must never have a commitment_id.
The AE review gate (POST /candidates/{id}/review) is the only
code path that sets commitment_id and creates a Commitment record.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Float, Enum as SAEnum, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
import enum


class CandidateVerdict(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    edited = "edited"
    dismissed = "dismissed"


class CommitmentType(str, enum.Enum):
    feature = "feature"
    date = "date"
    pricing = "pricing"
    security_compliance = "security_compliance"
    performance = "performance"
    sla = "sla"
    custom = "custom"
    other = "other"


class SeverityTier(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class CommitmentCandidate(Base):
    __tablename__ = "commitment_candidates"

    __table_args__ = (
        # Enforce: pending candidates cannot have a commitment_id
        CheckConstraint(
            "(verdict != 'pending') OR (commitment_id IS NULL)",
            name="chk_pending_no_commitment"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    # Extraction output
    raw_statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_passage: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_location: Mapped[str | None] = mapped_column(String, nullable=True)
    commitment_type: Mapped[CommitmentType] = mapped_column(SAEnum(CommitmentType), nullable=False)
    severity_tier: Mapped[SeverityTier] = mapped_column(SAEnum(SeverityTier), nullable=False)
    promisor: Mapped[str | None] = mapped_column(String, nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_due_date: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    classification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AE review gate — defaults to pending
    verdict: Mapped[CandidateVerdict] = mapped_column(
        SAEnum(CandidateVerdict), nullable=False, default=CandidateVerdict.pending
    )
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edited_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    dismiss_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Set only after AE confirmation — plain UUID, no FK constraint to avoid circular dependency
    # (commitments.candidate_id → commitment_candidates already covers integrity)
    commitment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
