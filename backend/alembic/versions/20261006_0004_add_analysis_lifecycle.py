"""add analysis lifecycle fields

Revision ID: 20261006_0004
Revises: 20261006_0003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261006_0004"
down_revision: Union[str, Sequence[str], None] = "20261006_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("analyses", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("analyses", sa.Column("duration_ms", sa.Float(), nullable=True))
    op.add_column("analyses", sa.Column("files_analyzed", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("analyses", sa.Column("analyzer_source", sa.String(length=32), nullable=False, server_default="static"))


def downgrade() -> None:
    op.drop_column("analyses", "analyzer_source")
    op.drop_column("analyses", "files_analyzed")
    op.drop_column("analyses", "duration_ms")
    op.drop_column("analyses", "completed_at")
    op.drop_column("analyses", "started_at")
