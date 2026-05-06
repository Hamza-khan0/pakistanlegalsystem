from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import IntelligenceArtifactType, IntelligenceStatus


def generate_intelligence_artifact_id() -> str:
    return uuid4().hex


class IntelligenceArtifact(Base):
    __tablename__ = "intelligence_artifacts"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_intelligence_artifact_id,
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    artifact_type: Mapped[IntelligenceArtifactType] = mapped_column(
        Enum(IntelligenceArtifactType, native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    structured_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="Local Chamber Intelligence", nullable=False)
    status: Mapped[IntelligenceStatus] = mapped_column(
        Enum(IntelligenceStatus, native_enum=False),
        default=IntelligenceStatus.GENERATED,
        nullable=False,
    )
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

    case: Mapped["Case"] = relationship(back_populates="intelligence_artifacts")
    document: Mapped["Document | None"] = relationship(back_populates="intelligence_artifacts")
    grounding_links: Mapped[list["GroundingLink"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
