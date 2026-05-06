"""Phase 4 chamber orchestration schema."""

from alembic import op
import sqlalchemy as sa


revision = "20260421_0003"
down_revision = "20260421_0002"
branch_labels = None
depends_on = None


chamber_task_type = sa.Enum(
    "summary",
    "issue_spotting",
    "preliminary_objections",
    "hearing_notes",
    "draft_outline",
    "draft_review",
    "research_memo",
    "procedural_check",
    name="chambertasktype",
    native_enum=False,
)
chamber_run_status = sa.Enum(
    "Queued",
    "Planning",
    "Running",
    "Critic Review",
    "Completed",
    "Failed",
    name="chamberrunstatus",
    native_enum=False,
)
chamber_run_step_status = sa.Enum(
    "Pending",
    "Running",
    "Completed",
    "Failed",
    name="chamberrunstepstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "chamber_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(length=64),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_type", chamber_task_type, nullable=False),
        sa.Column("user_instruction", sa.Text(), nullable=False, server_default=""),
        sa.Column("selected_workflow", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("status", chamber_run_status, nullable=False, server_default="Queued"),
        sa.Column("final_output", sa.Text(), nullable=False, server_default=""),
        sa.Column("final_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chamber_runs_case_id", "chamber_runs", ["case_id"], unique=False)

    op.create_table(
        "chamber_run_steps",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("chamber_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("task_label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("input_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("full_output", sa.Text(), nullable=False, server_default=""),
        sa.Column("structured_json", sa.JSON(), nullable=False),
        sa.Column("status", chamber_run_step_status, nullable=False, server_default="Pending"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("source_artifact_ids", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chamber_run_steps_run_id", "chamber_run_steps", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chamber_run_steps_run_id", table_name="chamber_run_steps")
    op.drop_table("chamber_run_steps")

    op.drop_index("ix_chamber_runs_case_id", table_name="chamber_runs")
    op.drop_table("chamber_runs")
