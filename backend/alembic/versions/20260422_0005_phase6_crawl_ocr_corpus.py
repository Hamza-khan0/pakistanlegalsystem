"""Phase 6 crawler, OCR, and corpus foundation."""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0005"
down_revision = "20260422_0004"
branch_labels = None
depends_on = None


crawl_source_type = sa.Enum(
    "HTML",
    "PDF",
    "Mixed",
    name="crawlsourcetype",
    native_enum=False,
)
crawl_mode = sa.Enum(
    "Index",
    "Paginated Index",
    "Detail Pages",
    "Direct Documents",
    name="crawlmode",
    native_enum=False,
)
crawl_job_status = sa.Enum(
    "Queued",
    "Running",
    "Completed",
    "Failed",
    name="crawljobstatus",
    native_enum=False,
)
crawl_document_status = sa.Enum(
    "Discovered",
    "Fetched",
    "Downloaded",
    "Duplicate",
    "Failed",
    name="crawldocumentstatus",
    native_enum=False,
)
crawl_processing_status = sa.Enum(
    "Pending",
    "Text Extracted",
    "OCR Required",
    "OCR Completed",
    "Partially Extracted",
    "Failed",
    name="crawlprocessingstatus",
    native_enum=False,
)
corpus_source_kind = sa.Enum(
    "Seeded Legal Source",
    "Crawled Document",
    name="corpussourcekind",
    native_enum=False,
)
dataset_split = sa.Enum(
    "train",
    "validation",
    "test",
    name="datasetsplit",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "crawl_sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", crawl_source_type, nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("allowed_domains", sa.JSON(), nullable=False),
        sa.Column("crawl_mode", crawl_mode, nullable=False),
        sa.Column("language_hint", sa.String(length=40), nullable=False, server_default="English"),
        sa.Column("category", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_crawl_sources_name"),
    )

    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("crawl_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", crawl_job_status, nullable=False, server_default="Queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pages_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_crawl_jobs_source_id", "crawl_jobs", ["source_id"], unique=False)

    op.create_table(
        "crawled_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("crawl_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "legal_source_id",
            sa.String(length=64),
            sa.ForeignKey("legal_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("document_type", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=40), nullable=False, server_default="Unknown"),
        sa.Column("jurisdiction", sa.String(length=120), nullable=False, server_default="Pakistan"),
        sa.Column("raw_html_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("downloaded_file_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(length=120), nullable=False, server_default="text/html"),
        sa.Column("crawl_status", crawl_document_status, nullable=False, server_default="Discovered"),
        sa.Column("processing_status", crawl_processing_status, nullable=False, server_default="Pending"),
        sa.Column("duplicate_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("extracted_text_preview", sa.Text(), nullable=False, server_default=""),
        sa.Column("normalized_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("ocr_engine", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("ocr_status", sa.String(length=120), nullable=False, server_default="Not Started"),
        sa.Column("ocr_confidence_summary", sa.Float(), nullable=True),
        sa.Column("language_detected", sa.String(length=40), nullable=False, server_default="Unknown"),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_json", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crawled_documents_source_id", "crawled_documents", ["source_id"], unique=False)
    op.create_index("ix_crawled_documents_legal_source_id", "crawled_documents", ["legal_source_id"], unique=False)
    op.create_index("ix_crawled_documents_source_url", "crawled_documents", ["source_url"], unique=False)
    op.create_index("ix_crawled_documents_duplicate_hash", "crawled_documents", ["duplicate_hash"], unique=False)

    op.create_table(
        "corpus_entries",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_kind", corpus_source_kind, nullable=False),
        sa.Column(
            "crawled_document_id",
            sa.String(length=64),
            sa.ForeignKey("crawled_documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "legal_source_id",
            sa.String(length=64),
            sa.ForeignKey("legal_sources.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=40), nullable=False, server_default="Unknown"),
        sa.Column("normalized_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ready_for_retrieval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ready_for_training", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dataset_split", dataset_split, nullable=False, server_default="train"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_corpus_entries_crawled_document_id", "corpus_entries", ["crawled_document_id"], unique=False)
    op.create_index("ix_corpus_entries_legal_source_id", "corpus_entries", ["legal_source_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_corpus_entries_legal_source_id", table_name="corpus_entries")
    op.drop_index("ix_corpus_entries_crawled_document_id", table_name="corpus_entries")
    op.drop_table("corpus_entries")

    op.drop_index("ix_crawled_documents_duplicate_hash", table_name="crawled_documents")
    op.drop_index("ix_crawled_documents_source_url", table_name="crawled_documents")
    op.drop_index("ix_crawled_documents_legal_source_id", table_name="crawled_documents")
    op.drop_index("ix_crawled_documents_source_id", table_name="crawled_documents")
    op.drop_table("crawled_documents")

    op.drop_index("ix_crawl_jobs_source_id", table_name="crawl_jobs")
    op.drop_table("crawl_jobs")

    op.drop_table("crawl_sources")
