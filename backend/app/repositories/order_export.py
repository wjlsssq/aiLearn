"""导出数据读取和快照存取，数据读取仍使用独立只读视图连接。"""

import json
from datetime import datetime, time, timedelta

from sqlalchemy import delete, exists, func, select, text

from ..core.config import settings
from ..db.agent_query import get_query_engine
from ..db.session import SessionLocal
from ..models import ChatMessage, ChatSession, User
from ..models.order_export import OrderExport


def read_rows(user_id, filters, columns, limit):
    clauses = [
        "user_id = :actor",
        f"{filters.date_field} >= :start",
        f"{filters.date_field} < :end",
    ]
    params = {
        "actor": user_id,
        "start": datetime.combine(filters.start_date, time.min),
        "end": datetime.combine(filters.end_date + timedelta(days=1), time.min),
        "limit": limit + 1,
    }
    if filters.status:
        clauses.append("status = :status")
        params["status"] = filters.status
    if filters.product:
        clauses.append("LOCATE(:product, product) > 0")
        params["product"] = filters.product
    # 列名和日期口径来自后端常量/枚举；用户文本只作为绑定值，不能注入 SQL。
    statement = (
        "SELECT "
        + ", ".join(columns)
        + " FROM agent_order_data WHERE "
        + " AND ".join(clauses)
        + f" ORDER BY {filters.date_field}, order_no LIMIT :limit"
    )
    with get_query_engine().connect() as db:
        db.execute(
            text("SET SESSION max_execution_time = :timeout"),
            {"timeout": settings.agent_query_timeout_ms},
        )
        return list(db.execute(text(statement), params).all())


def save_snapshot(record, now, quota):
    with SessionLocal.begin() as db:
        # 同一用户的并行导出共用用户行锁，避免同时通过配额检查。
        db.execute(
            select(User.id).where(User.id == record.user_id).with_for_update()
        ).one()
        db.execute(
            delete(OrderExport).where(
                OrderExport.user_id == record.user_id, OrderExport.expires_at <= now
            )
        )
        count = db.scalar(
            select(func.count())
            .select_from(OrderExport)
            .where(OrderExport.user_id == record.user_id)
        )
        if count >= quota:
            return False
        db.add(record)
    return True


def find_download(db, user_id, export_id, now):
    # 文件必须已经随成功问答持久化；失败/取消留下的临时快照不可下载。
    published = exists(
        select(ChatMessage.id)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(
            ChatSession.user_id == user_id,
            ChatMessage.role == "assistant",
            func.json_contains(
                ChatMessage.artifacts, json.dumps({"export_id": export_id})
            )
            == 1,
        )
    )
    return db.scalar(
        select(OrderExport).where(
            OrderExport.id == export_id,
            OrderExport.user_id == user_id,
            OrderExport.expires_at > now,
            published,
        )
    )


def purge_expired(now):
    with SessionLocal.begin() as db:
        return db.execute(
            delete(OrderExport).where(OrderExport.expires_at <= now)
        ).rowcount
