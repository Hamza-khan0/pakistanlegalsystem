from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import GroundingUsageType


def generate_grounding_link_id() -> str:
    return uuid4().hex


class GroundingLink(Base):
    __tablename__ = "grounding_links"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_grounding_link_id)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("chamber_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    artifact_id: Mapped[str | None] = mapped_column(
        ForeignKey("intelligence_artifacts.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    source_id: Mapped[str] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_id: Mapped[str | None] = mapped_column(
        ForeignKey("legal_source_chunks.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    usage_type: Mapped[GroundingUsageType] = mapped_column(
        Enum(GroundingUsageType, native_enum=False),
        default=GroundingUsageType.RETRIEVED,
        nullable=False,
    )
    excerpt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run: Mapped["ChamberRun | None"] = relationship(back_populates="grounding_links")
    artifact: Mapped["IntelligenceArtifact | None"] = relationship(back_populates="grounding_links")
    source: Mapped["LegalSource"] = relationship(back_populates="grounding_links")
    chunk: Mapped["LegalSourceChunk | None"] = relationship(back_populates="grounding_links")
