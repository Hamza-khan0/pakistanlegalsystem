"""phase7 ml prediction

Revision ID: 20260422_0006
Revises: 20260422_0005
Create Date: 2026-04-22 22:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0006"
down_revision = "20260422_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_datasets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.Enum("case_outcome", "maintainability", "risk_scoring", "case_type", name="mltaskname", native_enum=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.Enum("Ready", "Failed", name="mldatasetstatus", native_enum=False), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("label_strategy", sa.String(length=255), nullable=False),
        sa.Column("split_strategy", sa.String(length=255), nullable=False),
        sa.Column("data_path", sa.String(length=500), nullable=False),
        sa.Column("report_path", sa.String(length=500), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ml_datasets_task_name"), "ml_datasets", ["task_name"], unique=False)

    op.create_table(
        "ml_models",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.Enum("case_outcome", "maintainability", "risk_scoring", "case_type", name="mltaskname", native_enum=False), nullable=False),
        sa.Column("model_family", sa.Enum("Baseline", "Transformer", "Hybrid MLP", name="mlmodelfamily", native_enum=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Enum("Training", "Ready", "Failed", name="mlmodelstatus", native_enum=False), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("metrics_path", sa.String(length=500), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("label_schema", sa.JSON(), nullable=False),
        sa.Column("training_summary", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["ml_datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ml_models_dataset_id"), "ml_models", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_ml_models_task_name"), "ml_models", ["task_name"], unique=False)
    op.create_index(op.f("ix_ml_models_model_family"), "ml_models", ["model_family"], unique=False)

    op.create_table(
        "case_predictions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("task_name", sa.Enum("case_outcome", "maintainability", "risk_scoring", "case_type", name="mltaskname", native_enum=False), nullable=False),
        sa.Column("predicted_label", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("probabilities_json", sa.JSON(), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("warning_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_predictions_case_id"), "case_predictions", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_predictions_model_id"), "case_predictions", ["model_id"], unique=False)
    op.create_index(op.f("ix_case_predictions_task_name"), "case_predictions", ["task_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_predictions_task_name"), table_name="case_predictions")
    op.drop_index(op.f("ix_case_predictions_model_id"), table_name="case_predictions")
    op.drop_index(op.f("ix_case_predictions_case_id"), table_name="case_predictions")
    op.drop_table("case_predictions")
    op.drop_index(op.f("ix_ml_models_model_family"), table_name="ml_models")
    op.drop_index(op.f("ix_ml_models_task_name"), table_name="ml_models")
    op.drop_index(op.f("ix_ml_models_dataset_id"), table_name="ml_models")
    op.drop_table("ml_models")
    op.drop_index(op.f("ix_ml_datasets_task_name"), table_name="ml_datasets")
    op.drop_table("ml_datasets")
