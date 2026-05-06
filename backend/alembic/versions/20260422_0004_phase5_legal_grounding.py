"""Phase 5 legal grounding and retrieval schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0004"
down_revision = "20260421_0003"
branch_labels = None
depends_on = None


legal_source_type = sa.Enum(
    "Constitution",
    "Statute",
    "Rules",
    "Case Law",
    "Manual",
    name="legalsourcetype",
    native_enum=False,
)
grounding_usage_type = sa.Enum(
    "Retrieved",
    "Cited",
    "Relied On",
    "Suggested",
    name="groundingusagetype",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "legal_sources",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_type", legal_source_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_title", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("jurisdiction", sa.String(length=120), nullable=False, server_default="Pakistan"),
        sa.Column("category", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("act_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("section_label", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("section_number", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("order_rule_label", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="English"),
        sa.Column("citation_label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("normalized_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_legal_sources_title", "legal_sources", ["title"], unique=False)
    op.create_index("ix_legal_sources_short_title", "legal_sources", ["short_title"], unique=False)
    op.create_index("ix_legal_sources_category", "legal_sources", ["category"], unique=False)
    op.create_index("ix_legal_sources_act_name", "legal_sources", ["act_name"], unique=False)
    op.create_index("ix_legal_sources_section_label", "legal_sources", ["section_label"], unique=False)
    op.create_index("ix_legal_sources_section_number", "legal_sources", ["section_number"], unique=False)
    op.create_index("ix_legal_sources_citation_label", "legal_sources", ["citation_label"], unique=False)

    op.create_table(
        "legal_source_chunks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("legal_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("normalized_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_legal_source_chunks_source_id", "legal_source_chunks", ["source_id"], unique=False)

    op.create_table(
        "grounding_links",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("chamber_runs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "artifact_id",
            sa.String(length=64),
            sa.ForeignKey("intelligence_artifacts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "source_id",
            sa.String(length=64),
            sa.ForeignKey("legal_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            sa.String(length=64),
            sa.ForeignKey("legal_source_chunks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("usage_type", grounding_usage_type, nullable=False, server_default="Retrieved"),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_grounding_links_run_id", "grounding_links", ["run_id"], unique=False)
    op.create_index("ix_grounding_links_artifact_id", "grounding_links", ["artifact_id"], unique=False)
    op.create_index("ix_grounding_links_source_id", "grounding_links", ["source_id"], unique=False)
    op.create_index("ix_grounding_links_chunk_id", "grounding_links", ["chunk_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_grounding_links_chunk_id", table_name="grounding_links")
    op.drop_index("ix_grounding_links_source_id", table_name="grounding_links")
    op.drop_index("ix_grounding_links_artifact_id", table_name="grounding_links")
    op.drop_index("ix_grounding_links_run_id", table_name="grounding_links")
    op.drop_table("grounding_links")

    op.drop_index("ix_legal_source_chunks_source_id", table_name="legal_source_chunks")
    op.drop_table("legal_source_chunks")

    op.drop_index("ix_legal_sources_citation_label", table_name="legal_sources")
    op.drop_index("ix_legal_sources_section_number", table_name="legal_sources")
    op.drop_index("ix_legal_sources_section_label", table_name="legal_sources")
    op.drop_index("ix_legal_sources_act_name", table_name="legal_sources")
    op.drop_index("ix_legal_sources_category", table_name="legal_sources")
    op.drop_index("ix_legal_sources_short_title", table_name="legal_sources")
    op.drop_index("ix_legal_sources_title", table_name="legal_sources")
    op.drop_table("legal_sources")
