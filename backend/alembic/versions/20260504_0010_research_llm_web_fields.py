"""research llm web fields

Revision ID: 20260504_0010
Revises: 20260504_0009
Create Date: 2026-05-04 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0010"
down_revision: Union[str, Sequence[str], None] = "20260504_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("research_runs") as batch_op:
        batch_op.add_column(sa.Column("generated_draft_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("sources_by_origin_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("provider_metadata_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("live_web_used", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("llm_used_for_research", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("llm_used_for_drafting", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("research_runs") as batch_op:
        batch_op.drop_column("llm_used_for_drafting")
        batch_op.drop_column("llm_used_for_research")
        batch_op.drop_column("live_web_used")
        batch_op.drop_column("provider_metadata_json")
        batch_op.drop_column("sources_by_origin_json")
        batch_op.drop_column("generated_draft_json")
