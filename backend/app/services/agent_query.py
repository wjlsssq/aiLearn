"""参数校验、授权编译和审计闭环；不向模型返回数据库原始错误。"""

import json
import logging
from time import perf_counter

from sqlalchemy.exc import SQLAlchemyError

from ..core.errors import BusinessError
from ..core.order_query import compile_order_query
from ..repositories import agent as repository
from ..schemas.agent import QueryResult


def execute_order_query(user_id: int, request_id: str, sql: str) -> QueryResult:
    started = perf_counter()
    audit_id = repository.begin_audit(
        user_id, request_id, sql
    )  # 审计不可写时不执行查询。
    status, code, count = "failed", None, 0
    try:
        compiled = compile_order_query(sql, user_id)
        columns, rows, truncated = repository.query_orders(compiled)
        if len(json.dumps(rows, ensure_ascii=False).encode()) > 24000:
            raise ValueError("结果过大，请减少字段或返回条数")
        status, count = "succeeded", len(rows)
        return QueryResult(
            status="ok",
            message="已查询当前账号订单",
            columns=columns,
            rows=rows,
            truncated=truncated,
        )
    except ValueError as error:
        status, code = "rejected", "invalid_query"
        return QueryResult(status="rejected", message=str(error))
    except BusinessError:
        code = "not_configured"
        return QueryResult(
            status="unavailable", message="订单查询服务尚未就绪，请联系管理员"
        )
    except SQLAlchemyError as error:
        code = "database_error"
        logging.getLogger(__name__).warning("订单查询失败：%s", type(error).__name__)
        return QueryResult(
            status="rejected",
            message="查询执行失败；请检查字段与分组规则，或缩小查询范围后重试",
        )
    finally:
        repository.finish_audit(
            audit_id, status, int((perf_counter() - started) * 1000), count, code
        )
