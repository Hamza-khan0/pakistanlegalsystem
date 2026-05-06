"""Phase 3 intelligence layer schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260421_0002"
down_revision = "20260420_0001"
branch_labels = None
depends_on = None


intelligence_status = sa.Enum(
    "Not Processed",
    "Processing",
    "Processed",
    "Generated",
    "Stale",
    "Needs Review",
    "Failed",
    name="intelligencestatus",
    native_enum=False,
)
intelligence_artifact_type = sa.Enum(
    "Factual Summary",
    "Procedural Summary",
    "Issue Spotting",
    "Risk Assessment",
    "Draft Outline",
    "Preliminary Objections",
    "Petition Skeleton",
    "Reply Skeleton",
    "Hearing Note",
    "Case Memo",
    "Strategy Note",
    "Research Note",
    name="intelligenceartifacttype",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "intelligence_status",
            intelligence_status,
            nullable=False,
            server_default="Not Processed",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "documents",
        sa.Column("extraction_error", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "documents",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "intelligence_artifacts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(length=64),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.String(length=64),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("artifact_type", intelligence_artifact_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("status", intelligence_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_intelligence_artifacts_case_id", "intelligence_artifacts", ["case_id"], unique=False)
    op.create_index(
        "ix_intelligence_artifacts_document_id",
        "intelligence_artifacts",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_intelligence_artifacts_document_id", table_name="intelligence_artifacts")
    op.drop_index("ix_intelligence_artifacts_case_id", table_name="intelligence_artifacts")
    op.drop_table("intelligence_artifacts")

    op.drop_column("documents", "processed_at")
    op.drop_column("documents", "extraction_error")
    op.drop_column("documents", "extracted_text")
    op.drop_column("documents", "intelligence_status")
