from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MlModelFamily, MlModelStatus, MlTaskName


def generate_ml_model_id() -> str:
    return uuid4().hex


class MlModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_ml_model_id)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("ml_datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    task_name: Mapped[MlTaskName] = mapped_column(
        Enum(MlTaskName, native_enum=False),
        index=True,
        nullable=False,
    )
    model_family: Mapped[MlModelFamily] = mapped_column(
        Enum(MlModelFamily, native_enum=False),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[MlModelStatus] = mapped_column(
        Enum(MlModelStatus, native_enum=False),
        default=MlModelStatus.TRAINING,
        nullable=False,
    )
    artifact_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    metrics_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    label_schema: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    training_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
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

    dataset: Mapped["MlDataset"] = relationship(back_populates="models")
    predictions: Mapped[list["CasePrediction"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )
