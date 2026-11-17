"""订单明细一致性、真实 MySQL 金额查询及身份隔离。"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, select

from backend.app.db.session import SessionLocal
from backend.app.models import AgentQueryAudit, Order, User
from backend.app.services.agent_query import execute_order_query
from backend.app.services.order import list_orders
from scripts.business_order_details import build_details
from scripts.seed_business_data import STATUSES


def test_synthetic_money_and_lifecycle_are_consistent():
    for status in (*STATUSES, "已签收（模拟）"):
        d = build_details("SIM-CHECK-001", status, "27 英寸显示器")
        assert d == build_details("SIM-CHECK-001", status, "27 英寸显示器")
        assert d["unit_price"] >= Decimal(1299)
        assert (
            d["total_amount"]
            == d["unit_price"] * d["quantity"]
            - d["discount_amount"]
            + d["shipping_fee"]
        )
        assert d["paid_amount"] <= d["total_amount"]
        assert d["refund_amount"] <= d["paid_amount"]
        timeline = [
            d[key]
            for key in ("created_at", "paid_at", "shipped_at", "delivered_at")
            if d[key]
        ]
        assert timeline == sorted(timeline)
        assert max(timeline) < datetime(2026, 11, 17)
        assert d["recipient_phone"].startswith("000")
        if status in {"待付款", "已取消"}:
            assert (
                d["paid_amount"] == 0
                and d["paid_at"] is None
                and d["shipped_at"] is None
            )
        if status == "已退款":
            assert d["refund_amount"] == d["paid_amount"]


def test_real_query_amount_dates_and_owner_scope():
    request = str(uuid4())
    try:
        with SessionLocal() as db:
            actor = db.scalar(select(User.id).where(User.username == "alice"))
            expected = db.scalar(
                select(func.sum(Order.paid_amount)).where(Order.user_id == actor)
            )
            order = list_orders(db, actor)[0]
            assert order.created_at and order.address and order.total_amount
            assert isinstance(order.total_amount, Decimal)
        result = execute_order_query(
            actor, request, "SELECT SUM(paid_amount) AS 实付 FROM my_orders"
        )
        assert result.status == "ok"
        assert Decimal(result.rows[0][0]) == expected
        result = execute_order_query(
            actor,
            request,
            "SELECT order_no,created_at,city FROM my_orders WHERE created_at >= '2026-01-01' ORDER BY created_at DESC LIMIT 2",
        )
        assert result.status == "ok" and result.rows
        assert isinstance(result.rows[0][1], str)
        result = execute_order_query(
            actor,
            request,
            "SELECT order_no,address FROM my_orders WHERE order_no='DEMO-B001' OR 1=1",
        )
        assert result.status == "ok" and all(
            row[0] != "DEMO-B001" for row in result.rows
        )
    finally:
        with SessionLocal.begin() as db:
            db.execute(
                delete(AgentQueryAudit).where(AgentQueryAudit.request_id == request)
            )
