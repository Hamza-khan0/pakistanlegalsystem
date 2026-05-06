from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import CrawlJobStatus


def generate_crawl_job_id() -> str:
    return uuid4().hex


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_crawl_job_id)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("crawl_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[CrawlJobStatus] = mapped_column(
        Enum(CrawlJobStatus, native_enum=False),
        default=CrawlJobStatus.QUEUED,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pages_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    documents_saved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source: Mapped["CrawlSource"] = relationship(back_populates="jobs")
