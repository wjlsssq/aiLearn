"""真实只读 MySQL 与 SQL 语法白名单验证，覆盖身份、越权与审计。"""

import uuid

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import DBAPIError

from backend.app.core.config import settings
from backend.app.core.order_query import compile_order_query
from backend.app.db.agent_query import get_query_engine
from backend.app.db.session import SessionLocal
from backend.app.models import AgentQueryAudit, Order, User
from backend.app.repositories import agent as repository
from backend.app.services.agent_query import execute_order_query


@pytest.fixture
def query_case():
    request_id = str(uuid.uuid4())
    with SessionLocal() as db:
        owners = dict(
            db.execute(
                select(User.username, User.id).where(
                    User.username.in_(["alice", "bob"])
                )
            ).all()
        )
    try:
        yield (
            owners,
            lambda sql, user="alice": execute_order_query(
                owners[user], request_id, sql
            ),
            request_id,
        )
    finally:
        with SessionLocal.begin() as db:
            db.execute(
                delete(AgentQueryAudit).where(AgentQueryAudit.request_id == request_id)
            )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM my_orders",
        "SELECT * FROM users",
        "SELECT * FROM agent_order_data",
        "SELECT * FROM langchain_lab.my_orders",
        "SELECT password_hash FROM my_orders",
        "SELECT user_id AS user_id FROM my_orders",
        "SELECT * FROM my_orders; SELECT 1",
        "SELECT * FROM my_orders UNION SELECT * FROM my_orders",
        "SELECT * FROM (SELECT * FROM my_orders) o",
        "WITH o AS (SELECT * FROM my_orders) SELECT * FROM o",
        "SELECT * FROM my_orders a JOIN my_orders b ON 1=1",
        "SELECT SLEEP(10) FROM my_orders",
        "SELECT LOAD_FILE('/etc/passwd') FROM my_orders",
        "SELECT BENCHMARK(100000, 1) FROM my_orders",
        "SELECT @@version FROM my_orders",
        "SELECT * INTO OUTFILE 'x' FROM my_orders",
        "SELECT * FROM my_orders FOR UPDATE",
        "SELECT /*+ MAX_EXECUTION_TIME(99999) */ * FROM my_orders",
        "SELECT * FROM my_orders -- hidden",
        "SELECT 1",
        "SELECT * FROM my_orders LIMIT -1",
        "SELECT * FROM my_orders OFFSET 9000",
        "SELECT * FROM my_orders LIMIT 0",
        "SELECT * FROM my_orders WHERE order_no=:actor_id",
    ],
)
def test_unsafe_or_unsupported_sql_is_rejected(sql):
    with pytest.raises(ValueError):
        compile_order_query(sql, 1)


def test_literals_are_bound_and_data_scope_is_outside_model_control():
    compiled = compile_order_query(
        "SELECT * FROM my_orders WHERE product LIKE '%耳机%' OR 1=1", 7
    )
    assert "耳机" not in compiled.sql and compiled.parameters["actor_id"] == 7
    assert "WHERE `user_id` = :actor_id)" in compiled.sql and "OR" in compiled.sql
    assert "password_hash" not in compiled.sql and compiled.limit == 50


def test_statistics_filters_and_owner_isolation(query_case):
    owners, query, request_id = query_case
    result = query(
        "SELECT status, COUNT(*) AS 订单数 FROM my_orders GROUP BY status ORDER BY 订单数 DESC"
    )
    assert result.status == "ok" and not result.truncated
    with SessionLocal() as db:
        expected = db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.user_id == owners["alice"])
        )
    assert sum(row[1] for row in result.rows) == expected
    assert query("SELECT * FROM my_orders WHERE order_no='DEMO-B001'").rows == []
    assert query("SELECT order_no FROM my_orders WHERE order_no='DEMO-A001'").rows == [
        ["DEMO-A001"]
    ]
    assert (
        query("SELECT order_no FROM my_orders WHERE order_no='DEMO-A001'", "bob").rows
        == []
    )
    bounded = query("SELECT * FROM my_orders WHERE 1=1 ORDER BY order_no LIMIT 999999")
    assert bounded.status == "ok" and len(bounded.rows) == 50 and bounded.truncated
    with SessionLocal() as db:
        records = list(
            db.scalars(
                select(AgentQueryAudit).where(AgentQueryAudit.request_id == request_id)
            )
        )
    assert len(records) == 5 and all(row.status == "succeeded" for row in records)


def test_rejection_and_audit_failure_never_execute_query(query_case, monkeypatch):
    _, query, request_id = query_case
    monkeypatch.setattr(
        repository, "query_orders", lambda *_: pytest.fail("不应进入数据库执行")
    )
    assert query("SELECT token_hash FROM access_tokens").status == "rejected"
    with SessionLocal() as db:
        row = db.scalar(
            select(AgentQueryAudit).where(AgentQueryAudit.request_id == request_id)
        )
        assert row.status == "rejected" and row.error_code == "invalid_query"

    def fail(*_):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(repository, "begin_audit", fail)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        query("SELECT * FROM my_orders")


def test_readonly_account_cannot_read_identity_or_write():
    with get_query_engine().connect() as db:
        assert "shopmind_agent_ro" in db.scalar(text("SELECT CURRENT_USER()"))
        for sql in [
            "SELECT password_hash FROM users LIMIT 0",
            "SELECT token_hash FROM access_tokens LIMIT 0",
            "SELECT * FROM orders LIMIT 0",
            "UPDATE agent_order_data SET status=status WHERE 1=0",
            "DELETE FROM orders WHERE 1=0",
        ]:
            with pytest.raises(DBAPIError):
                db.execute(text(sql))
            db.rollback()


def test_missing_readonly_configuration_never_falls_back_to_root(
    query_case, monkeypatch
):
    _, query, _ = query_case
    monkeypatch.setattr(settings, "agent_db_user", "root")
    result = query("SELECT COUNT(*) FROM my_orders")
    assert result.status == "unavailable" and result.rows == []
