from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import (
    DocumentStatus,
    DocumentType,
    ExtractionStatus,
    IntelligenceStatus,
    OcrStatus,
    ParsingStatus,
)


def generate_document_id() -> str:
    return uuid4().hex


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_document_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False),
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        default=DocumentStatus.REFERENCE,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, native_enum=False),
        default=ExtractionStatus.READY_FOR_INDEXING,
        nullable=False,
    )
    ocr_status: Mapped[OcrStatus] = mapped_column(
        Enum(OcrStatus, native_enum=False),
        default=OcrStatus.NOT_STARTED,
        nullable=False,
    )
    parsing_status: Mapped[ParsingStatus] = mapped_column(
        Enum(ParsingStatus, native_enum=False),
        default=ParsingStatus.NOT_STARTED,
        nullable=False,
    )
    intelligence_status: Mapped[IntelligenceStatus] = mapped_column(
        Enum(IntelligenceStatus, native_enum=False),
        default=IntelligenceStatus.NOT_PROCESSED,
        nullable=False,
    )
    extracted_text_preview: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extraction_error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    filed_by: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship(back_populates="documents")
    intelligence_artifacts: Mapped[list["IntelligenceArtifact"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
