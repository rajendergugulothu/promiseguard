import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ConflictType(str, enum.Enum):
    cross_customer = "cross_customer"          # same commitment, different terms, different accounts
    cross_document = "cross_document"          # commitment contradicts contract or another doc
    date_infeasible = "date_infeasible"        # due date < capability readiness date (deterministic)
    capability_gap = "capability_gap"          # depends on unsupported capability
    self_contradiction = "self_contradiction"  # contradicts another commitment in same account


class ConflictStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class Conflict(Base):
    __tablename__ = "conflicts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    commitment_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commitments.id"), nullable=False)
    commitment_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commitments.id"), nullable=True
    )  # null for capability_gap type
    conflict_type: Mapped[ConflictType] = mapped_column(SAEnum(ConflictType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[ConflictStatus] = mapped_column(SAEnum(ConflictStatus), nullable=False, default=ConflictStatus.open)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
