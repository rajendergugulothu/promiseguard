"""
CapabilityRegistry — product capability catalogue.
CapabilityMatch — semantic link from commitment to capability.

CRITICAL: unknown != unsupported.
Four distinct states in CapabilityStatus:
  current     — capability exists and is supported today
  on_roadmap  — planned, with a roadmap date
  unsupported — explicitly not planned
  unknown     — no match found OR roadmap data incomplete

Never collapse unknown to unsupported. Different risk implication.
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Text, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from database import Base
import enum


class CapabilityStatus(str, enum.Enum):
    current = "current"
    on_roadmap = "on_roadmap"
    unsupported = "unsupported"
    unknown = "unknown"  # explicitly distinct from unsupported


class CapabilityRegistry(Base):
    __tablename__ = "capability_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CapabilityStatus] = mapped_column(
        SAEnum(CapabilityStatus), nullable=False, default=CapabilityStatus.unknown
    )
    roadmap_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    roadmap_confidence: Mapped[str | None] = mapped_column(String, nullable=True)  # high/medium/low/unknown
    owner_team: Mapped[str | None] = mapped_column(String, nullable=True)
    source_system: Mapped[str | None] = mapped_column(String, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CapabilityMatch(Base):
    __tablename__ = "capability_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commitment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commitments.id"), nullable=False)
    capability_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capability_registry.id"), nullable=True
    )  # null = no match found
    match_status: Mapped[CapabilityStatus] = mapped_column(SAEnum(CapabilityStatus), nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    roadmap_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    matched_by: Mapped[str] = mapped_column(String, nullable=False, default="system")
    match_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
