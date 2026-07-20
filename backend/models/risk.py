import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Float, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class AlertTrigger(str, enum.Enum):
    deadline_30d = "deadline_30d"
    deadline_7d = "deadline_7d"
    deadline_1d = "deadline_1d"
    dependency_slipped = "dependency_slipped"
    new_conflict = "new_conflict"
    status_at_risk = "status_at_risk"
    high_risk_unowned = "high_risk_unowned"
    commitment_missed = "commitment_missed"


class AlertRecipientType(str, enum.Enum):
    owner = "owner"
    account_csm = "account_csm"
    legal_reviewer = "legal_reviewer"
    executive = "executive"


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commitment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commitments.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    severity_weight: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_factor: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility_factor: Mapped[float] = mapped_column(Float, nullable=False)
    arr_exposure_factor: Mapped[float] = mapped_column(Float, nullable=False)
    open_conflicts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    commitment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commitments.id"), nullable=False)
    trigger_type: Mapped[AlertTrigger] = mapped_column(SAEnum(AlertTrigger), nullable=False)
    recipient_type: Mapped[AlertRecipientType] = mapped_column(SAEnum(AlertRecipientType), nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
