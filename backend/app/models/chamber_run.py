from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ChamberRunStatus, ChamberTaskType


def generate_chamber_run_id() -> str:
    return uuid4().hex


class ChamberRun(Base):
    __tablename__ = "chamber_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_chamber_run_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    task_type: Mapped[ChamberTaskType] = mapped_column(
        Enum(ChamberTaskType, native_enum=False),
        nullable=False,
    )
    user_instruction: Mapped[str] = mapped_column(Text, default="", nullable=False)
    selected_workflow: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    status: Mapped[ChamberRunStatus] = mapped_column(
        Enum(ChamberRunStatus, native_enum=False),
        default=ChamberRunStatus.QUEUED,
        nullable=False,
    )
    final_output: Mapped[str] = mapped_column(Text, default="", nullable=False)
    final_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="chamber_runs")
    steps: Mapped[list["ChamberRunStep"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ChamberRunStep.step_order",
    )
    grounding_links: Mapped[list["GroundingLink"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
