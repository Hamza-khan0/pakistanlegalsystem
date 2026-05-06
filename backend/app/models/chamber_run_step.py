from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ChamberRunStepStatus


def generate_chamber_run_step_id() -> str:
    return uuid4().hex


class ChamberRunStep(Base):
    __tablename__ = "chamber_run_steps"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_chamber_run_step_id,
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("chamber_runs.id", ondelete="CASCADE"),
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    task_label: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    full_output: Mapped[str] = mapped_column(Text, default="", nullable=False)
    structured_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[ChamberRunStepStatus] = mapped_column(
        Enum(ChamberRunStepStatus, native_enum=False),
        default=ChamberRunStepStatus.PENDING,
        nullable=False,
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_artifact_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped["ChamberRun"] = relationship(back_populates="steps")
