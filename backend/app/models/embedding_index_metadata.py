from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.enums import EmbeddingIndexStatus, RetrievalMode


def generate_embedding_index_id() -> str:
    return uuid4().hex


class EmbeddingIndexMetadata(Base):
    __tablename__ = "embedding_index_metadata"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_embedding_index_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    retrieval_mode: Mapped[RetrievalMode] = mapped_column(
        Enum(RetrievalMode, native_enum=False),
        nullable=False,
        default=RetrievalMode.SEMANTIC,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[EmbeddingIndexStatus] = mapped_column(
        Enum(EmbeddingIndexStatus, native_enum=False),
        nullable=False,
        default=EmbeddingIndexStatus.BUILDING,
    )
    corpus_version: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    index_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
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
