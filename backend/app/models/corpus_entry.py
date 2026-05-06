from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import CorpusSourceKind, DatasetSplit


def generate_corpus_entry_id() -> str:
    return uuid4().hex


class CorpusEntry(Base):
    __tablename__ = "corpus_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_corpus_entry_id)
    source_kind: Mapped[CorpusSourceKind] = mapped_column(
        Enum(CorpusSourceKind, native_enum=False),
        nullable=False,
    )
    crawled_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawled_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    legal_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    language: Mapped[str] = mapped_column(String(40), default="Unknown", nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ready_for_retrieval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ready_for_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dataset_split: Mapped[DatasetSplit] = mapped_column(
        Enum(DatasetSplit, native_enum=False),
        default=DatasetSplit.TRAIN,
        nullable=False,
    )
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

    crawled_document: Mapped["CrawledDocument | None"] = relationship(back_populates="corpus_entries")
    legal_source: Mapped["LegalSource | None"] = relationship(back_populates="corpus_entries")
