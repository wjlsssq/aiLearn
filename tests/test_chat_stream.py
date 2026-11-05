"""真实 MySQL + 可控增量模型，验证流式事件、失败、取消与提交边界。"""

import asyncio  # 使用真实异步生成器检查取消，不请求外部模型。
from contextlib import aclosing  # 显式模拟客户端关闭业务流。
import hashlib  # 精确清理本测试创建的令牌。
import json  # 读取实际 SSE 事件。
import uuid  # 每个测试拥有独立会话标题。
import pytest  # 注入模型与故障。
from fastapi.testclient import TestClient  # 调用真实认证、流式路由和响应编码。
from sqlalchemy import delete, select
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.errors import BusinessError
from backend.app.db.session import SessionLocal
from backend.app.models import AccessToken, User, ChatSession, ChatMessage
from backend.app.repositories import chat as repository
from backend.app.schemas.chat import ChatInput
from backend.app.services import chat as service


@pytest.fixture
def stream_case(monkeypatch):
    monkeypatch.setattr(
        settings, "chat_mode", "mock"
    )  # 元数据明确标记为模拟，隔离真实密钥。
    question = "stream-test-" + uuid.uuid4().hex[:16]
    tokens = []
    with TestClient(app) as client:
        for name in ("alice", "bob"):
            response = client.post(
                "/api/login", json={"username": name, "password": "Learn123!"}
            )
            assert response.status_code == 200
            tokens.append(response.json()["token"])
        try:
            yield (
                client,
                question,
                {"Authorization": "Bearer " + tokens[0]},
                {"Authorization": "Bearer " + tokens[1]},
            )
        finally:
            with SessionLocal.begin() as db:
                ids = list(
                    db.scalars(
                        select(ChatSession.id).where(ChatSession.title == question)
                    )
                )
                if ids:
                    db.execute(
                        delete(ChatMessage).where(ChatMessage.session_id.in_(ids))
                    )
                    db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
                for token in tokens:
                    db.execute(
                        delete(AccessToken).where(
                            AccessToken.token_hash
                            == hashlib.sha256(token.encode()).hexdigest()
                        )
                    )


def decode_events(response):
    events = []
    for frame in response.text.strip().split("\n\n"):
        name, data = frame.split("\n", 1)
        events.append(
            (name.removeprefix("event: "), json.loads(data.removeprefix("data: ")))
        )
    return events


def session_exists(question):
    with SessionLocal() as db:
        return (
            db.scalar(select(ChatSession.id).where(ChatSession.title == question))
            is not None
        )


def test_stream_deltas_precede_atomic_save(stream_case, monkeypatch):
    client, question, alice, _ = stream_case
    options = []

    async def model(content, **prompt):
        options.append(prompt)
        for text in ("第一段", " ", "第二段\n结束"):
            assert not session_exists(
                question
            )  # 任何增量产生时都未保存空会话或半条问答。
            yield text

    monkeypatch.setattr(service, "stream_reply", model)
    response = client.post(
        "/api/chat/stream",
        headers=alice,
        json={
            "message": question,
            "prompt": {"store_name": "流式店", "style": "detailed"},
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-accel-buffering"] == "no"
    events = decode_events(response)
    assert [name for name, _ in events] == ["start", "delta", "delta", "delta", "done"]
    assert options == [{"store_name": "流式店", "style": "detailed"}]
    result = events[-1][1]
    assert result["reply"] == "第一段 第二段\n结束" and result["mode"] == "mock"
    history = client.get(
        f"/api/sessions/{result['session_id']}/messages", headers=alice
    ).json()
    assert [row["content"] for row in history] == [question, result["reply"]]


@pytest.mark.parametrize("unexpected", [False, True])
def test_partial_failure_emits_safe_error_and_saves_nothing(
    stream_case, monkeypatch, unexpected
):
    client, question, alice, _ = stream_case

    async def model(content, **options):
        yield "部分正文"
        if unexpected:
            raise RuntimeError("private-provider-secret")
        raise BusinessError(504, "模型响应超时")

    monkeypatch.setattr(service, "stream_reply", model)
    response = client.post(
        "/api/chat/stream", headers=alice, json={"message": question}
    )
    events = decode_events(response)
    assert [name for name, _ in events] == ["start", "delta", "error"]
    assert events[-1][1]["status"] == (500 if unexpected else 504)
    assert "private-provider-secret" not in response.text
    assert not session_exists(question)


def test_disconnect_closes_model_and_does_not_save(stream_case, monkeypatch):
    _, question, _, _ = stream_case
    closed = []

    async def model(content, **options):
        try:
            yield "只收到第一段"
            await asyncio.Event().wait()  # 模拟等待供应商下一块。
        finally:
            closed.append(True)

    monkeypatch.setattr(service, "stream_reply", model)

    async def disconnect():
        with SessionLocal() as db:
            user_id = db.scalar(select(User.id).where(User.username == "alice"))
            prepared = service.prepare_stream(db, user_id, ChatInput(message=question))
            assert not db.in_transaction()  # 模型等待期间不持有认证或会话查询事务。
        async with aclosing(service.stream_message(prepared)) as events:
            assert (await anext(events))[0] == "start"
            assert (await anext(events))[0] == "delta"
            task = asyncio.create_task(anext(events))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(disconnect())
    assert closed == [True]
    assert not session_exists(question)


def test_stream_authorization_precedes_model_call(stream_case, monkeypatch):
    client, question, alice, bob = stream_case
    called = []

    async def model(content, **options):
        called.append(True)
        yield "不应调用"

    monkeypatch.setattr(service, "stream_reply", model)
    with SessionLocal.begin() as db:
        user_id = db.scalar(select(User.id).where(User.username == "alice"))
        session_id = repository.create_session(db, user_id, question).id
    assert (
        client.post("/api/chat/stream", json={"message": question}).status_code == 401
    )
    assert (
        client.post(
            "/api/chat/stream", headers=alice, json={"message": "   "}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/chat/stream",
            headers=bob,
            json={"message": question, "session_id": session_id},
        ).status_code
        == 404
    )
    assert not called


def test_database_failure_rolls_back_before_done(stream_case, monkeypatch):
    client, question, alice, _ = stream_case
    original = repository.add_exchange

    async def model(content, **options):
        yield "模型已经生成完毕"

    def fail_write(db, session_id, content, reply):
        original(db, session_id, content, reply)
        raise RuntimeError("private-database-detail")  # 创建会话后故障也必须整笔回滚。

    monkeypatch.setattr(service, "stream_reply", model)
    monkeypatch.setattr(repository, "add_exchange", fail_write)
    response = client.post(
        "/api/chat/stream", headers=alice, json={"message": question}
    )
    assert [name for name, _ in decode_events(response)] == ["start", "delta", "error"]
    assert "private-database-detail" not in response.text
    assert not session_exists(question)
