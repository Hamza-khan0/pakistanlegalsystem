from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ResearchRunStatus


def generate_research_run_id() -> str:
    return uuid4().hex


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_research_run_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    status: Mapped[ResearchRunStatus] = mapped_column(
        Enum(ResearchRunStatus, native_enum=False),
        default=ResearchRunStatus.PENDING,
        index=True,
        nullable=False,
    )
    workflow_type: Mapped[str] = mapped_column(String(120), default="research_draft_pipeline", nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    detected_issues_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    query_plan_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    retrieved_sources_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    research_memo_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generated_draft_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    critic_report_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    drafting_instructions_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sources_by_origin_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provider_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    live_web_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_used_for_research: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_used_for_drafting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    markdown_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="research_runs")
