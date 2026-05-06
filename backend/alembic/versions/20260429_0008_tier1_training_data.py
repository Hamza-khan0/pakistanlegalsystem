"""tier1 training data preparation

Revision ID: 20260429_0008
Revises: 20260423_0007
Create Date: 2026-04-29 01:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0008"
down_revision: Union[str, Sequence[str], None] = "20260423_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tier1_documents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=700), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=40), nullable=False),
        sa.Column("document_type", sa.String(length=120), nullable=False),
        sa.Column("court", sa.String(length=255), nullable=False),
        sa.Column("date", sa.String(length=80), nullable=False),
        sa.Column("citation", sa.String(length=255), nullable=False),
        sa.Column("case_number", sa.String(length=255), nullable=False),
        sa.Column("parties", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("import_status", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tier1_documents_source_type"), "tier1_documents", ["source_type"], unique=False)
    op.create_index(op.f("ix_tier1_documents_source_name"), "tier1_documents", ["source_name"], unique=False)
    op.create_index(op.f("ix_tier1_documents_external_id"), "tier1_documents", ["external_id"], unique=False)
    op.create_index(op.f("ix_tier1_documents_language"), "tier1_documents", ["language"], unique=False)
    op.create_index(op.f("ix_tier1_documents_document_type"), "tier1_documents", ["document_type"], unique=False)
    op.create_index(op.f("ix_tier1_documents_import_status"), "tier1_documents", ["import_status"], unique=False)

    op.create_table(
        "tier1_labels",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.Enum("case_outcome", "maintainability", "risk_scoring", "case_type", name="mltaskname", native_enum=False), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("label_source", sa.String(length=120), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["tier1_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "task_name", name="uq_tier1_labels_document_task"),
    )
    op.create_index(op.f("ix_tier1_labels_document_id"), "tier1_labels", ["document_id"], unique=False)
    op.create_index(op.f("ix_tier1_labels_task_name"), "tier1_labels", ["task_name"], unique=False)
    op.create_index(op.f("ix_tier1_labels_label"), "tier1_labels", ["label"], unique=False)
    op.create_index(op.f("ix_tier1_labels_label_source"), "tier1_labels", ["label_source"], unique=False)
    op.create_index(op.f("ix_tier1_labels_needs_review"), "tier1_labels", ["needs_review"], unique=False)
    op.create_index(op.f("ix_tier1_labels_reviewed"), "tier1_labels", ["reviewed"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tier1_labels_reviewed"), table_name="tier1_labels")
    op.drop_index(op.f("ix_tier1_labels_needs_review"), table_name="tier1_labels")
    op.drop_index(op.f("ix_tier1_labels_label_source"), table_name="tier1_labels")
    op.drop_index(op.f("ix_tier1_labels_label"), table_name="tier1_labels")
    op.drop_index(op.f("ix_tier1_labels_task_name"), table_name="tier1_labels")
    op.drop_index(op.f("ix_tier1_labels_document_id"), table_name="tier1_labels")
    op.drop_table("tier1_labels")
    op.drop_index(op.f("ix_tier1_documents_import_status"), table_name="tier1_documents")
    op.drop_index(op.f("ix_tier1_documents_document_type"), table_name="tier1_documents")
    op.drop_index(op.f("ix_tier1_documents_language"), table_name="tier1_documents")
    op.drop_index(op.f("ix_tier1_documents_external_id"), table_name="tier1_documents")
    op.drop_index(op.f("ix_tier1_documents_source_name"), table_name="tier1_documents")
    op.drop_index(op.f("ix_tier1_documents_source_type"), table_name="tier1_documents")
    op.drop_table("tier1_documents")
