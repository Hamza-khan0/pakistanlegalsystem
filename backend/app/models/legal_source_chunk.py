from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


def generate_legal_source_chunk_id() -> str:
    return uuid4().hex


class LegalSourceChunk(Base):
    __tablename__ = "legal_source_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_legal_source_chunk_id)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source: Mapped["LegalSource"] = relationship(back_populates="chunks")
    grounding_links: Mapped[list["GroundingLink"]] = relationship(back_populates="chunk")
