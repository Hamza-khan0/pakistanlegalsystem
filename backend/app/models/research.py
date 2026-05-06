from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ResearchStatus


def generate_research_id() -> str:
    return uuid4().hex


class ResearchEntry(Base):
    __tablename__ = "research_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_research_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    citations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_type: Mapped[str] = mapped_column(String(120), default="Internal Research", nullable=False)
    status: Mapped[ResearchStatus] = mapped_column(
        Enum(ResearchStatus, native_enum=False),
        default=ResearchStatus.FRESH,
        nullable=False,
    )
    author: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    next_question: Mapped[str] = mapped_column(Text, default="", nullable=False)
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

    case: Mapped["Case"] = relationship(back_populates="research_entries")
