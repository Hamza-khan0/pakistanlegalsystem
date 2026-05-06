from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MlDatasetStatus, MlTaskName


def generate_ml_dataset_id() -> str:
    return uuid4().hex


class MlDataset(Base):
    __tablename__ = "ml_datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_ml_dataset_id)
    task_name: Mapped[MlTaskName] = mapped_column(
        Enum(MlTaskName, native_enum=False),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[MlDatasetStatus] = mapped_column(
        Enum(MlDatasetStatus, native_enum=False),
        default=MlDatasetStatus.READY,
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    label_strategy: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    split_strategy: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    data_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    report_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
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

    models: Mapped[list["MlModel"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
