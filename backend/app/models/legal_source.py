from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import LegalSourceType


def generate_legal_source_id() -> str:
    return uuid4().hex


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_legal_source_id)
    source_type: Mapped[LegalSourceType] = mapped_column(
        Enum(LegalSourceType, native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_title: Mapped[str] = mapped_column(String(180), default="", nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(120), default="Pakistan", nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    act_name: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    section_label: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    section_number: Mapped[str] = mapped_column(String(80), default="", nullable=False, index=True)
    order_rule_label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="English", nullable=False)
    citation_label: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
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

    chunks: Mapped[list["LegalSourceChunk"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="LegalSourceChunk.chunk_index",
    )
    grounding_links: Mapped[list["GroundingLink"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
    crawled_documents: Mapped[list["CrawledDocument"]] = relationship(
        back_populates="legal_source",
    )
    corpus_entries: Mapped[list["CorpusEntry"]] = relationship(
        back_populates="legal_source",
        cascade="all, delete-orphan",
    )
