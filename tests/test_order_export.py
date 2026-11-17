"""真实 MySQL 导出、文件协议、归属隔离与 Excel 文本安全。"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from time import time
from uuid import uuid4
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, select, update

from backend.app.core.errors import BusinessError
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import (
    AgentQueryAudit,
    ChatMessage,
    ChatSession,
    Order,
    OrderExport,
    User,
)
from backend.app.repositories.chat import add_exchange
from backend.app.schemas.order_export import OrderExportInput
from backend.app.services import order_export as service
from scripts.business_order_details import build_details


@pytest.fixture
def export_case(monkeypatch):
    request = str(uuid4())
    monkeypatch.setattr(service, "uuid4", lambda: request)
    sessions = []
    order_numbers = []
    with SessionLocal() as db:
        owners = dict(
            db.execute(
                select(User.username, User.id).where(
                    User.username.in_(["alice", "bob"])
                )
            ).all()
        )
    filters = OrderExportInput(start_date="2040-01-01", end_date="2040-01-02")
    try:
        with SessionLocal.begin() as db:
            for index, stamp in enumerate(
                [
                    datetime(2040, 1, 1),
                    datetime(2040, 1, 2, 23, 59, 59),
                    datetime(2040, 1, 3),
                ]
            ):
                number = "EX-" + uuid4().hex[:24]
                order_numbers.append(number)
                values = build_details(number, "已完成", "测试商品")
                values["created_at"] = stamp
                db.add(
                    Order(
                        order_no=number,
                        user_id=owners["alice"],
                        product="=危险文本",
                        status="已完成",
                        **values,
                    )
                )

        def publish(artifact):
            with SessionLocal.begin() as db:
                session = ChatSession(user_id=owners["alice"], title="导出测试")
                db.add(session)
                db.flush()
                sessions.append(session.id)
                add_exchange(
                    db,
                    session.id,
                    "导出订单",
                    "已生成",
                    [artifact.model_dump(mode="json")],
                )

        yield owners, request, filters, publish
    finally:
        with SessionLocal.begin() as db:
            db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(sessions)))
            db.execute(delete(ChatSession).where(ChatSession.id.in_(sessions)))
            # 只清理本测试创建的导出，不触及其他真实会话文件。
            db.execute(delete(OrderExport).where(OrderExport.id == request))
            db.execute(
                delete(AgentQueryAudit).where(AgentQueryAudit.request_id == request)
            )
            db.execute(delete(Order).where(Order.order_no.in_(order_numbers)))


def test_export_inclusive_dates_authenticated_download_and_expiry(export_case):
    owners, request, filters, publish = export_case
    artifact = service.create_export(owners["alice"], request, filters)
    assert artifact.row_count == 2  # 包含结束日 23:59:59，不包含下一天零点。
    assert (
        service.repository.read_rows(owners["bob"], filters, service.COLUMNS, 5000)
        == []
    )
    injected = filters.model_copy(update={"product": "' OR 1=1 --"})
    assert (
        service.repository.read_rows(owners["alice"], injected, service.COLUMNS, 5000)
        == []
    )
    with SessionLocal() as db, pytest.raises(BusinessError):
        service.download_export(
            db, owners["alice"], artifact.export_id
        )  # 取消/未保存问答不可下载。
    publish(artifact)
    with TestClient(app) as client:
        url = f"/api/order-exports/{artifact.export_id}/download"
        assert client.get(url).status_code == 401
        tokens = []
        try:
            for user, expected in [("alice", 200), ("bob", 404)]:
                token = client.post(
                    "/api/login", json={"username": user, "password": "Learn123!"}
                ).json()["token"]
                tokens.append(token)
                response = client.get(url, headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == expected
                if expected == 200:
                    assert "spreadsheetml" in response.headers["content-type"]
                    assert response.headers["cache-control"] == "no-store"
                    assert "filename*=UTF-8" in response.headers["content-disposition"]
                    with ZipFile(BytesIO(response.content)) as workbook:
                        sheet = workbook.read("xl/worksheets/sheet1.xml").decode()
                        assert (
                            "<f>" not in sheet
                            and "autoFilter" in sheet
                            and "frozen" in sheet
                        )
                        assert '<row r="3"' in sheet and '<row r="4"' not in sheet
                        assert (
                            "=危险文本"
                            in workbook.read("xl/sharedStrings.xml").decode()
                        )
            with SessionLocal.begin() as db:
                db.execute(
                    update(OrderExport)
                    .where(OrderExport.id == artifact.export_id)
                    .values(expires_at=int(time()) - 1)
                )
            assert (
                client.get(
                    url, headers={"Authorization": f"Bearer {tokens[0]}"}
                ).status_code
                == 404
            )
        finally:
            for token in tokens:
                client.post("/api/logout", headers={"Authorization": f"Bearer {token}"})


def test_export_rejects_truncation_and_enforces_filters(export_case, monkeypatch):
    owners, request, filters, publish = export_case
    monkeypatch.setattr(service, "MAX_EXPORT_ROWS", 1)
    with pytest.raises(BusinessError, match="超过 5000"):
        service.create_export(owners["alice"], request, filters)
    monkeypatch.setattr(service, "MAX_EXPORT_ROWS", 5000)
    empty = filters.model_copy(update={"status": "待付款"})
    artifact = service.create_export(owners["alice"], request, empty)
    assert artifact.row_count == 0
    publish(artifact)
    with SessionLocal() as db:
        _, payload = service.download_export(db, owners["alice"], artifact.export_id)
    assert ZipFile(BytesIO(payload)).testzip() is None


def test_export_quota_and_safe_string_cells(export_case, monkeypatch):
    owners, request, filters, _ = export_case
    monkeypatch.setattr(service, "MAX_ACTIVE_EXPORTS", 0)
    with pytest.raises(BusinessError, match="有效导出"):
        service.create_export(owners["alice"], request, filters)
    row = ["=1+1", "+cmd", "@外链", 2, Decimal("19.90")] + [None] * (
        len(service.COLUMNS) - 5
    )
    payload = service.build_workbook([row], filters, int(time()))
    with ZipFile(BytesIO(payload)) as workbook:
        sheet = workbook.read("xl/worksheets/sheet1.xml").decode()
        assert "<f>" not in sheet and "<v>19.9</v>" in sheet
        assert not any("externalLinks/" in name for name in workbook.namelist())


@pytest.mark.parametrize(
    "arguments",
    [
        {"start_date": "2026-11-02", "end_date": "2026-11-01"},
        {"start_date": "2020-01-01", "end_date": "2026-01-01"},
        {"start_date": "2099-12-31", "end_date": "2100-01-01"},
        {"start_date": "2026-01-01", "end_date": "2026-01-31", "date_field": "user_id"},
        {"start_date": "2026-01-01", "end_date": "2026-01-31", "user_id": 2},
    ],
)
def test_export_filter_validation(arguments):
    with pytest.raises(ValidationError):
        OrderExportInput.model_validate(arguments)
