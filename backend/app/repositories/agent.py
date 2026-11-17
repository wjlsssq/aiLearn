"""只读查询与查询审计的数据访问。"""

import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text, update

from ..core.config import settings
from ..core.order_query import CompiledOrderQuery
from ..db.agent_query import get_query_engine
from ..db.session import SessionLocal
from ..models import AgentQueryAudit


def begin_audit(user_id: int, request_id: str, sql: str) -> int:
    with SessionLocal.begin() as db:
        record = AgentQueryAudit(
            user_id=user_id,
            request_id=request_id,
            query_text=sql[:2000],
            status="pending",
            row_count=0,
            elapsed_ms=0,
            created_at=int(time.time()),
        )
        db.add(record)
        db.flush()
        return record.id


def finish_audit(
    audit_id: int,
    status: str,
    elapsed_ms: int,
    rows: int = 0,
    error_code: str | None = None,
):
    with SessionLocal.begin() as db:
        db.execute(
            update(AgentQueryAudit)
            .where(AgentQueryAudit.id == audit_id)
            .values(
                status=status,
                elapsed_ms=elapsed_ms,
                row_count=rows,
                error_code=error_code,
            )
        )


def query_orders(compiled: CompiledOrderQuery) -> tuple[list[str], list[list], bool]:
    with get_query_engine().connect() as db:
        # 超时由后端设置，模型无权覆盖。只读账号还只能 SELECT 一个裁剪列的视图。
        db.execute(
            text("SET SESSION max_execution_time = :timeout"),
            {"timeout": settings.agent_query_timeout_ms},
        )
        result = db.execute(text(compiled.sql), compiled.parameters)
        columns = list(result.keys())
        rows = [
            [
                str(value) if isinstance(value, (Decimal, datetime, date)) else value
                for value in row
            ]
            for row in result
        ]
    return columns, rows[: compiled.limit], len(rows) > compiled.limit
