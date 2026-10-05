"""create repository files table

Revision ID: 20261006_0002
Revises: 20261006_0001
Create Date: 2026-10-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261006_0002"
down_revision: Union[str, Sequence[str], None] = "20261006_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repository_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=4096), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("is_binary", sa.Boolean(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "path", name="uq_repository_files_repository_path"),
    )
    op.create_index(
        "ix_repository_files_repository_id", "repository_files", ["repository_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_repository_files_repository_id", table_name="repository_files")
    op.drop_table("repository_files")
