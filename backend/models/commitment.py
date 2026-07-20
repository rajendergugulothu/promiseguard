"""
Commitment — post-AE-review confirmed records only.

CRITICAL CHECK CONSTRAINT:
security_compliance commitments cannot have legal_review_status='not_required'.
Enforced at the database level. No application code can bypass this.
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Text, Numeric, Enum as SAEnum, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from models.candidate import CommitmentType, SeverityTier
import enum


class CommitmentStatus(str, enum.Enum):
    proposed = "proposed"
    confirmed = "confirmed"
    in_progress = "in_progress"
    at_risk = "at_risk"
    fulfilled = "fulfilled"
    disputed = "disputed"
    missed = "missed"


class LegalReviewStatus(str, enum.Enum):
    not_required = "not_required"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class DateConfidence(str, enum.Enum):
    confirmed = "confirmed"
    inferred = "inferred"
    unknown = "unknown"


class Commitment(Base):
    __tablename__ = "commitments"

    __table_args__ = (
        # LEGAL GATE: security_compliance commitments cannot skip legal review
        CheckConstraint(
            "commitment_type != 'security_compliance' OR legal_review_status != 'not_required'",
            name="chk_legal_review_required"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commitment_candidates.id"), nullable=False)

    # Core commitment
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_passage: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_location: Mapped[str | None] = mapped_column(String, nullable=True)
    commitment_type: Mapped[CommitmentType] = mapped_column(SAEnum(CommitmentType), nullable=False)
    severity_tier: Mapped[SeverityTier] = mapped_column(SAEnum(SeverityTier), nullable=False)

    # Parties
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    account_name: Mapped[str] = mapped_column(String, nullable=False)
    promisor: Mapped[str | None] = mapped_column(String, nullable=True)
    responsible_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_contact: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timeline
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date_confidence: Mapped[DateConfidence] = mapped_column(
        SAEnum(DateConfidence), nullable=False, default=DateConfidence.unknown
    )
    raw_due_date_text: Mapped[str | None] = mapped_column(String, nullable=True)

    # Dependencies
    dependency_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status FSM
    status: Mapped[CommitmentStatus] = mapped_column(
        SAEnum(CommitmentStatus), nullable=False, default=CommitmentStatus.proposed
    )
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Revenue
    arr_exposure: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Legal gate — enforced by CHECK constraint above
    legal_review_status: Mapped[LegalReviewStatus] = mapped_column(
        SAEnum(LegalReviewStatus), nullable=False, default=LegalReviewStatus.not_required
    )

    # Fulfilment
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fulfilled_by: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
