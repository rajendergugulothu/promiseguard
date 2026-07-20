import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Date, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
import enum


class SourceType(str, enum.Enum):
    gong_transcript = "gong_transcript"
    email_thread = "email_thread"
    contract = "contract"
    implementation_notes = "implementation_notes"
    slack_export = "slack_export"
    document_upload = "document_upload"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    account_name: Mapped[str] = mapped_column(String, nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    source_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
