from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MlTaskName


def generate_case_prediction_id() -> str:
    return uuid4().hex


class CasePrediction(Base):
    __tablename__ = "case_predictions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_case_prediction_id)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_id: Mapped[str] = mapped_column(
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    task_name: Mapped[MlTaskName] = mapped_column(
        Enum(MlTaskName, native_enum=False),
        index=True,
        nullable=False,
    )
    predicted_label: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    probabilities_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warning_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship(back_populates="predictions")
    model: Mapped["MlModel"] = relationship(back_populates="predictions")
