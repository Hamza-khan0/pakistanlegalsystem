"""phase 8 semantic retrieval metadata

Revision ID: 20260423_0007
Revises: 20260422_0006
Create Date: 2026-04-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260423_0007"
down_revision: Union[str, Sequence[str], None] = "20260422_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("grounding_links") as batch_op:
        batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.create_table(
        "embedding_index_metadata",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("retrieval_mode", sa.Enum("Lexical", "Semantic", "Hybrid", name="retrievalmode", native_enum=False), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Enum("Building", "Ready", "Failed", name="embeddingindexstatus", native_enum=False), nullable=False),
        sa.Column("corpus_version", sa.String(length=120), nullable=False),
        sa.Column("index_path", sa.String(length=500), nullable=False),
        sa.Column("vector_dimension", sa.Integer(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_embedding_index_metadata_name"), "embedding_index_metadata", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_embedding_index_metadata_name"), table_name="embedding_index_metadata")
    op.drop_table("embedding_index_metadata")
    with op.batch_alter_table("grounding_links") as batch_op:
        batch_op.drop_column("metadata_json")
