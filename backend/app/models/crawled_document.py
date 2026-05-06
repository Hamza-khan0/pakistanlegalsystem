from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import CrawlDocumentStatus, CrawlProcessingStatus


def generate_crawled_document_id() -> str:
    return uuid4().hex


class CrawledDocument(Base):
    __tablename__ = "crawled_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_crawled_document_id)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("crawl_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    legal_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    document_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    language: Mapped[str] = mapped_column(String(40), default="Unknown", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(120), default="Pakistan", nullable=False)
    raw_html_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    downloaded_file_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="text/html", nullable=False)
    crawl_status: Mapped[CrawlDocumentStatus] = mapped_column(
        Enum(CrawlDocumentStatus, native_enum=False),
        default=CrawlDocumentStatus.DISCOVERED,
        nullable=False,
    )
    processing_status: Mapped[CrawlProcessingStatus] = mapped_column(
        Enum(CrawlProcessingStatus, native_enum=False),
        default=CrawlProcessingStatus.PENDING,
        nullable=False,
    )
    duplicate_hash: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_text_preview: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ocr_engine: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(120), default="Not Started", nullable=False)
    ocr_confidence_summary: Mapped[float | None] = mapped_column(Float, nullable=True)
    language_detected: Mapped[str] = mapped_column(String(40), default="Unknown", nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    source: Mapped["CrawlSource"] = relationship(back_populates="documents")
    legal_source: Mapped["LegalSource | None"] = relationship(back_populates="crawled_documents")
    corpus_entries: Mapped[list["CorpusEntry"]] = relationship(
        back_populates="crawled_document",
        cascade="all, delete-orphan",
    )
