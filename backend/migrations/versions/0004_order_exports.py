"""持久化有时效与归属限制的 Excel 导出快照。"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import MEDIUMBLOB

revision = "0004_order_exports"
down_revision = "0003_order_details"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order_exports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(128), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("payload", MEDIUMBLOB(), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_order_exports_user_id", "order_exports", ["user_id"])
    op.create_index("ix_order_exports_expires_at", "order_exports", ["expires_at"])


def downgrade():
    op.drop_table("order_exports")
