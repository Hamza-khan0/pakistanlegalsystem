from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import CrawlMode, CrawlSourceType


def generate_crawl_source_id() -> str:
    return uuid4().hex


class CrawlSource(Base):
    __tablename__ = "crawl_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_crawl_source_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_type: Mapped[CrawlSourceType] = mapped_column(
        Enum(CrawlSourceType, native_enum=False),
        nullable=False,
    )
    base_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    allowed_domains: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    crawl_mode: Mapped[CrawlMode] = mapped_column(
        Enum(CrawlMode, native_enum=False),
        nullable=False,
    )
    language_hint: Mapped[str] = mapped_column(String(40), default="English", nullable=False)
    category: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
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

    jobs: Mapped[list["CrawlJob"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="CrawlJob.started_at.desc()",
    )
    documents: Mapped[list["CrawledDocument"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="CrawledDocument.updated_at.desc()",
    )
