"""Agent 查询审计、消息业务结果与只读订单视图。"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON

revision = "0002_agent_chat"
down_revision = "0001_knowledge"
branch_labels = None
depends_on = None


def upgrade():
    columns = {
        column["name"]: column
        for column in sa.inspect(op.get_bind()).get_columns("chat_messages")
    }
    if "artifacts" not in columns:
        op.add_column("chat_messages", sa.Column("artifacts", JSON(), nullable=True))
    elif (
        not isinstance(columns["artifacts"]["type"], JSON)
        or not columns["artifacts"]["nullable"]
    ):
        raise RuntimeError("chat_messages.artifacts 与预期 JSON 可空字段不兼容")
    # 新开发库 create_all 可能已有当前 ORM 字段；旧库仍通过本迁移增量添加。
    op.create_table(
        "agent_query_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query_text", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(32), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index(
        "ix_agent_query_audits_request_id", "agent_query_audits", ["request_id"]
    )
    op.create_index("ix_agent_query_audits_user_id", "agent_query_audits", ["user_id"])
    op.execute(
        "CREATE SQL SECURITY DEFINER VIEW agent_order_data AS SELECT user_id, order_no, product, status FROM orders"
    )
    # 视图只提供业务列；执行器会把模型逻辑表替换成当前用户的派生查询。


def downgrade():
    op.execute("DROP VIEW agent_order_data")
    op.drop_table("agent_query_audits")
    op.drop_column("chat_messages", "artifacts")
