"""Initial schema for AI Legal Chambers Phase 2."""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0001"
down_revision = None
branch_labels = None
depends_on = None


case_status = sa.Enum(
    "Active",
    "Hearing Due",
    "Awaiting Filing",
    "Research",
    "Drafting",
    "Closed",
    name="casestatus",
    native_enum=False,
)
priority_level = sa.Enum(
    "Critical",
    "High",
    "Medium",
    "Low",
    name="prioritylevel",
    native_enum=False,
)
document_type = sa.Enum(
    "Plaint",
    "Written Statement",
    "Affidavit",
    "Rejoinder",
    "Application",
    "Annexure",
    "Order Sheet",
    "Judgment",
    "Vakalatnama",
    "Brief",
    name="documenttype",
    native_enum=False,
)
document_status = sa.Enum(
    "Filed",
    "Draft",
    "Under Review",
    "Pending Signature",
    "Reference",
    name="documentstatus",
    native_enum=False,
)
extraction_status = sa.Enum(
    "Parsed",
    "OCR Running",
    "Manual Review",
    "Ready for Indexing",
    name="extractionstatus",
    native_enum=False,
)
ocr_status = sa.Enum(
    "Not Started",
    "Queued",
    "Completed",
    name="ocrstatus",
    native_enum=False,
)
parsing_status = sa.Enum(
    "Not Started",
    "In Progress",
    "Completed",
    name="parsingstatus",
    native_enum=False,
)
timeline_event_type = sa.Enum(
    "Filing",
    "Hearing",
    "Notice",
    "Research",
    "Draft",
    "Order",
    name="timelineeventtype",
    native_enum=False,
)
note_type = sa.Enum(
    "Internal Note",
    "Client Note",
    "Strategy Note",
    "Hearing Note",
    name="notetype",
    native_enum=False,
)
research_status = sa.Enum(
    "Fresh",
    "Verified",
    "Needs Review",
    name="researchstatus",
    native_enum=False,
)
draft_status = sa.Enum(
    "Drafting",
    "Reviewing",
    "Ready for Filing",
    name="draftstatus",
    native_enum=False,
)
agent_run_status = sa.Enum(
    "Queued",
    "Running",
    "Completed",
    "Needs Review",
    "Failed",
    name="agentrunstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("case_number", sa.String(length=120), nullable=False),
        sa.Column("forum", sa.String(length=255), nullable=False),
        sa.Column("matter_type", sa.String(length=120), nullable=False),
        sa.Column("status", case_status, nullable=False),
        sa.Column("priority", priority_level, nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("opposing_party", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("legal_issues", sa.JSON(), nullable=False),
        sa.Column("relief_sought", sa.JSON(), nullable=False),
        sa.Column("next_hearing_date", sa.Date(), nullable=True),
        sa.Column("assigned_counsel", sa.JSON(), nullable=False),
        sa.Column("filing_stage", sa.String(length=255), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=False),
        sa.Column("important_notes", sa.JSON(), nullable=False),
        sa.Column("facts_background", sa.JSON(), nullable=False),
        sa.Column("linked_statutes", sa.JSON(), nullable=False),
        sa.Column("precedents", sa.JSON(), nullable=False),
        sa.Column("procedural_alerts", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cases_case_number", "cases", ["case_number"], unique=True)
    op.create_index("ix_cases_forum", "cases", ["forum"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document_type", document_type, nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("upload_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("extraction_status", extraction_status, nullable=False),
        sa.Column("ocr_status", ocr_status, nullable=False),
        sa.Column("parsing_status", parsing_status, nullable=False),
        sa.Column("extracted_text_preview", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("filed_by", sa.String(length=120), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_case_id", "documents", ["case_id"], unique=False)

    op.create_table(
        "timeline_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("event_type", timeline_event_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_timeline_events_case_id", "timeline_events", ["case_id"], unique=False)

    op.create_table(
        "notes",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("note_type", note_type, nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notes_case_id", "notes", ["case_id"], unique=False)

    op.create_table(
        "research_entries",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("source_type", sa.String(length=120), nullable=False),
        sa.Column("status", research_status, nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("next_question", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_entries_case_id", "research_entries", ["case_id"], unique=False)

    op.create_table(
        "drafts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("draft_type", sa.String(length=120), nullable=False),
        sa.Column("status", draft_status, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drafts_case_id", "drafts", ["case_id"], unique=False)

    op.create_table(
        "agent_run_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("case_id", sa.String(length=64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=120), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("status", agent_run_status, nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("next_action", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_agent_run_logs_case_id", "agent_run_logs", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_run_logs_case_id", table_name="agent_run_logs")
    op.drop_table("agent_run_logs")
    op.drop_index("ix_drafts_case_id", table_name="drafts")
    op.drop_table("drafts")
    op.drop_index("ix_research_entries_case_id", table_name="research_entries")
    op.drop_table("research_entries")
    op.drop_index("ix_notes_case_id", table_name="notes")
    op.drop_table("notes")
    op.drop_index("ix_timeline_events_case_id", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_index("ix_documents_case_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_cases_forum", table_name="cases")
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_table("cases")
