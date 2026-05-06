from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import CaseStatus, PriorityLevel


def generate_id() -> str:
    return uuid4().hex


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    case_number: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    forum: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    matter_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, native_enum=False),
        default=CaseStatus.ACTIVE,
        nullable=False,
    )
    priority: Mapped[PriorityLevel] = mapped_column(
        Enum(PriorityLevel, native_enum=False),
        default=PriorityLevel.MEDIUM,
        nullable=False,
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    opposing_party: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    legal_issues: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    relief_sought: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    next_hearing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_counsel: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    filing_stage: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    important_notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    facts_background: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    linked_statutes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    precedents: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    procedural_alerts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    documents: Mapped[list["Document"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    research_entries: Mapped[list["ResearchEntry"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    research_runs: Mapped[list["ResearchRun"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    drafts: Mapped[list["Draft"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    agent_run_logs: Mapped[list["AgentRunLog"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    intelligence_artifacts: Mapped[list["IntelligenceArtifact"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    chamber_runs: Mapped[list["ChamberRun"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[list["CasePrediction"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
