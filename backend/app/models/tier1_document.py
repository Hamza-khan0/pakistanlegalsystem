from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


def generate_tier1_document_id() -> str:
    return uuid4().hex


class Tier1Document(Base):
    __tablename__ = "tier1_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_tier1_document_id)
    source_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), default="", index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(700), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language: Mapped[str] = mapped_column(String(40), default="Unknown", index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(120), default="Judgment", index=True, nullable=False)
    court: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    date: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    citation: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    case_number: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    parties: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    import_status: Mapped[str] = mapped_column(String(80), default="Imported", index=True, nullable=False)
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

    labels: Mapped[list["Tier1Label"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
