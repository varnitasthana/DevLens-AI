"""store repository source content for retrieval

Revision ID: 20261006_0006
Revises: 20261006_0005
"""

from alembic import op
import sqlalchemy as sa

revision = "20261006_0006"
down_revision = "20261006_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("repository_files", sa.Column("content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("repository_files", "content")
