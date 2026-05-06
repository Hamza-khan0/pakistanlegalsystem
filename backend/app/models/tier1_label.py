from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MlTaskName


def generate_tier1_label_id() -> str:
    return uuid4().hex


class Tier1Label(Base):
    __tablename__ = "tier1_labels"
    __table_args__ = (
        UniqueConstraint("document_id", "task_name", name="uq_tier1_labels_document_task"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_tier1_label_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("tier1_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    task_name: Mapped[MlTaskName] = mapped_column(
        Enum(MlTaskName, native_enum=False),
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    label_source: Mapped[str] = mapped_column(String(120), default="weak_supervision", index=True, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
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

    document: Mapped["Tier1Document"] = relationship(back_populates="labels")
