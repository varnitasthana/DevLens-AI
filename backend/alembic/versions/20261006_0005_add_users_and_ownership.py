"""add users and repository ownership"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = "20261006_0005"
down_revision: Union[str, Sequence[str], None] = "20261006_0004"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.add_column("repositories", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_repositories_owner_id", "repositories", ["owner_id"], unique=False)
    op.create_foreign_key("fk_repositories_owner_id_users", "repositories", "users", ["owner_id"], ["id"], ondelete="CASCADE")
def downgrade() -> None:
    op.drop_constraint("fk_repositories_owner_id_users", "repositories", type_="foreignkey")
    op.drop_index("ix_repositories_owner_id", table_name="repositories")
    op.drop_column("repositories", "owner_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
