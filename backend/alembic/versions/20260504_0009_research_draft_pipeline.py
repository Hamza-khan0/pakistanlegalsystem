"""research draft pipeline runs

Revision ID: 20260504_0009
Revises: 20260429_0008
Create Date: 2026-05-04 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0009"
down_revision: Union[str, Sequence[str], None] = "20260429_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "completed_with_warnings",
                "failed",
                name="researchrunstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("workflow_type", sa.String(length=120), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("detected_issues_json", sa.JSON(), nullable=False),
        sa.Column("query_plan_json", sa.JSON(), nullable=False),
        sa.Column("retrieved_sources_json", sa.JSON(), nullable=False),
        sa.Column("research_memo_json", sa.JSON(), nullable=False),
        sa.Column("critic_report_json", sa.JSON(), nullable=False),
        sa.Column("drafting_instructions_json", sa.JSON(), nullable=False),
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        sa.Column("pdf_path", sa.String(length=700), nullable=True),
        sa.Column("markdown_path", sa.String(length=700), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_runs_case_id"), "research_runs", ["case_id"], unique=False)
    op.create_index(op.f("ix_research_runs_status"), "research_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_research_runs_status"), table_name="research_runs")
    op.drop_index(op.f("ix_research_runs_case_id"), table_name="research_runs")
    op.drop_table("research_runs")
