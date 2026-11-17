"""补齐订单金额、生命周期、收货与物流字段，保留旧记录。"""

import sqlalchemy as sa
from alembic import op

revision = "0003_order_details"
down_revision = "0002_agent_chat"
branch_labels = None
depends_on = None


def upgrade():
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("orders")}
    if "quantity" not in existing:
        op.add_column(
            "orders", sa.Column("quantity", sa.Integer(), nullable=True, comment="数量")
        )
    if "unit_price" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "unit_price", sa.Numeric(12, 2), nullable=True, comment="商品单价（元）"
            ),
        )
    if "discount_amount" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "discount_amount",
                sa.Numeric(12, 2),
                nullable=True,
                comment="优惠金额（元）",
            ),
        )
    if "shipping_fee" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "shipping_fee", sa.Numeric(12, 2), nullable=True, comment="运费（元）"
            ),
        )
    if "total_amount" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "total_amount",
                sa.Numeric(12, 2),
                nullable=True,
                comment="应付金额（元）",
            ),
        )
    if "paid_amount" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "paid_amount",
                sa.Numeric(12, 2),
                nullable=True,
                comment="实付金额（元）",
            ),
        )
    if "refund_amount" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "refund_amount",
                sa.Numeric(12, 2),
                nullable=True,
                comment="已退款金额（元）",
            ),
        )
    if "created_at" not in existing:
        op.add_column(
            "orders",
            sa.Column("created_at", sa.DateTime(), nullable=True, comment="下单时间"),
        )
    if "paid_at" not in existing:
        op.add_column(
            "orders",
            sa.Column("paid_at", sa.DateTime(), nullable=True, comment="付款时间"),
        )
    if "shipped_at" not in existing:
        op.add_column(
            "orders",
            sa.Column("shipped_at", sa.DateTime(), nullable=True, comment="发货时间"),
        )
    if "delivered_at" not in existing:
        op.add_column(
            "orders",
            sa.Column("delivered_at", sa.DateTime(), nullable=True, comment="签收时间"),
        )
    if "recipient_name" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "recipient_name", sa.String(64), nullable=True, comment="合成收货人"
            ),
        )
    if "recipient_phone" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "recipient_phone", sa.String(32), nullable=True, comment="合成联系电话"
            ),
        )
    if "province" not in existing:
        op.add_column(
            "orders",
            sa.Column("province", sa.String(32), nullable=True, comment="收货省份"),
        )
    if "city" not in existing:
        op.add_column(
            "orders",
            sa.Column("city", sa.String(32), nullable=True, comment="收货城市"),
        )
    if "district" not in existing:
        op.add_column(
            "orders",
            sa.Column("district", sa.String(32), nullable=True, comment="收货区县"),
        )
    if "address" not in existing:
        op.add_column(
            "orders",
            sa.Column("address", sa.String(256), nullable=True, comment="收货详细地址"),
        )
    if "shipping_company" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "shipping_company", sa.String(64), nullable=True, comment="物流公司"
            ),
        )
    if "tracking_no" not in existing:
        op.add_column(
            "orders",
            sa.Column(
                "tracking_no", sa.String(64), nullable=True, comment="合成物流单号"
            ),
        )
    op.create_index("ix_orders_user_created", "orders", ["user_id", "created_at"])
    op.execute(
        "CREATE OR REPLACE SQL SECURITY DEFINER VIEW agent_order_data AS SELECT user_id, order_no, product, status, quantity, unit_price, discount_amount, shipping_fee, total_amount, paid_amount, refund_amount, created_at, paid_at, shipped_at, delivered_at, recipient_name, recipient_phone, province, city, district, address, shipping_company, tracking_no FROM orders"
    )


def downgrade():
    op.execute(
        "CREATE OR REPLACE SQL SECURITY DEFINER VIEW agent_order_data AS SELECT user_id, order_no, product, status FROM orders"
    )
    op.drop_index("ix_orders_user_created", table_name="orders")
    op.drop_column("orders", "tracking_no")
    op.drop_column("orders", "shipping_company")
    op.drop_column("orders", "address")
    op.drop_column("orders", "district")
    op.drop_column("orders", "city")
    op.drop_column("orders", "province")
    op.drop_column("orders", "recipient_phone")
    op.drop_column("orders", "recipient_name")
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "shipped_at")
    op.drop_column("orders", "paid_at")
    op.drop_column("orders", "created_at")
    op.drop_column("orders", "refund_amount")
    op.drop_column("orders", "paid_amount")
    op.drop_column("orders", "total_amount")
    op.drop_column("orders", "shipping_fee")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "unit_price")
    op.drop_column("orders", "quantity")
