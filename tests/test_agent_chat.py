"""真实 create_agent、供应商适配器与 MySQL；所有模型请求均在内存中响应。"""

import asyncio
import hashlib
import json
import uuid
from contextlib import aclosing

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, select

from backend.app.ai.models import factory
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import (
    AccessToken,
    AgentQueryAudit,
    ChatMessage,
    ChatSession,
    User,
)
from backend.app.schemas.chat import ChatInput
from backend.app.services import agent_chat, chat


def call(
    sql="SELECT order_no FROM my_orders WHERE order_no='DEMO-A001'",
    *,
    name="query_my_orders",
    arguments=None,
    id="call-query-1",
):
    return {
        "index": 0,
        "id": id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(
                {"sql": sql} if arguments is None else arguments, ensure_ascii=False
            ),
        },
    }


@pytest.fixture
def agent_case(monkeypatch):
    identifier = str(uuid.uuid4())
    question = "agent-test-" + identifier[:16]
    monkeypatch.setattr(agent_chat, "uuid4", lambda: identifier)
    for key, value in {
        "chat_mode": "llm",
        "llm_model": "test-model",
        "llm_base_url": "https://model.test/v1",
        "llm_api_key": SecretStr("test-only-key"),
    }.items():
        monkeypatch.setattr(settings, key, value)
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    tokens, clients, requests, closed = [], [], [], []

    def install(script, provider="deepseek"):
        monkeypatch.setattr(settings, "llm_provider", provider)
        name = "ChatDeepSeek" if provider == "deepseek" else "ChatOpenAI"
        original = getattr(factory, name)

        def handle(request):
            body = json.loads(request.content)
            requests.append(body)
            if not body.get("stream"):
                return httpx.Response(
                    200,
                    json={
                        "id": "draft",
                        "object": "chat.completion",
                        "created": 0,
                        "model": "test-model",
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": json.dumps(
                                        {
                                            "order_no": "DEMO-A001",
                                            "issue_type": "return",
                                            "reason": "耳机损坏",
                                            "quantity": 1,
                                        }
                                    ),
                                },
                            }
                        ],
                    },
                )
            model_calls = sum(bool(item.get("stream")) for item in requests)
            response = script(body, model_calls)
            if response.get("status", 200) != 200:
                return httpx.Response(
                    response["status"],
                    json={"error": {"message": "private test-only-key"}},
                )
            delta = {"role": "assistant", "content": response.get("text")}
            if response.get("calls"):
                delta["tool_calls"] = response["calls"]

            def frame(value, finish=None):
                return (
                    "data: "
                    + json.dumps(
                        {
                            "id": f"model-{model_calls}",
                            "object": "chat.completion.chunk",
                            "created": 0,
                            "model": "test-model",
                            "choices": [
                                {"index": 0, "delta": value, "finish_reason": finish}
                            ],
                        },
                        ensure_ascii=False,
                    )
                    + "\n\n"
                ).encode()

            if response.get("hang"):

                class HangingStream(httpx.AsyncByteStream):
                    async def __aiter__(self):
                        try:
                            yield frame(delta)
                            await asyncio.Event().wait()
                        finally:
                            closed.append(True)

                return httpx.Response(
                    200,
                    headers={"content-type": "text/event-stream"},
                    stream=HangingStream(),
                )
            data = (
                frame(delta)
                + frame(
                    {},
                    response.get(
                        "finish", "tool_calls" if response.get("calls") else "stop"
                    ),
                )
                + b"data: [DONE]\n\n"
            )
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=data
            )

        transport = httpx.MockTransport(handle)
        sync, asynchronous = (
            httpx.Client(transport=transport),
            httpx.AsyncClient(transport=transport),
        )
        clients.extend([sync, asynchronous])
        monkeypatch.setattr(
            factory,
            name,
            lambda **opts: original(
                **opts, http_client=sync, http_async_client=asynchronous
            ),
        )

    with TestClient(app) as client:
        for username in ("alice", "bob"):
            response = client.post(
                "/api/login", json={"username": username, "password": "Learn123!"}
            )
            assert response.status_code == 200
            tokens.append(response.json()["token"])
        try:
            yield (
                client,
                [{"Authorization": "Bearer " + token} for token in tokens],
                question,
                install,
                requests,
                closed,
            )
        finally:
            with SessionLocal.begin() as db:
                ids = list(
                    db.scalars(
                        select(ChatSession.id).where(
                            ChatSession.title.startswith(question, autoescape=True)
                        )
                    )
                )
                if ids:
                    db.execute(
                        delete(ChatMessage).where(ChatMessage.session_id.in_(ids))
                    )
                    db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
                db.execute(
                    delete(AgentQueryAudit).where(
                        AgentQueryAudit.request_id == identifier
                    )
                )
                db.execute(
                    delete(AccessToken).where(
                        AccessToken.token_hash.in_(
                            [
                                hashlib.sha256(token.encode()).hexdigest()
                                for token in tokens
                            ]
                        )
                    )
                )
    for connection in clients:
        if isinstance(connection, httpx.AsyncClient):
            with asyncio.Runner() as runner:
                runner.run(connection.aclose())
        else:
            connection.close()


def decode(response):
    return [
        (frame.split("\n", 1)[0][7:], json.loads(frame.split("\n", 1)[1][6:]))
        for frame in response.text.strip().split("\n\n")
    ]


@pytest.mark.parametrize("provider", ["deepseek", "openai_compatible"])
def test_chat_queries_persists_cards_and_recovers_history(agent_case, provider):
    client, (alice, bob), question, install, requests, _ = agent_case
    install(
        lambda body, _: (
            {"text": "先查询", "calls": [call()]}
            if body["messages"][-1]["role"] == "user"
            else {"text": "查询完成，请查看订单。"}
        ),
        provider,
    )
    events = decode(
        client.post("/api/chat/stream", headers=alice, json={"message": question})
    )
    assert events[-1][0] == "done", events
    result = events[-1][1]
    assert result["reply"] == "查询完成，请查看订单。"
    assert result["artifacts"][0]["rows"] == [["DEMO-A001"]]
    assert any(name == "activity" for name, _ in events) and any(
        name == "answer_reset" for name, _ in events
    )
    messages = requests[1]["messages"]
    assert (
        messages[-1]["role"] == "tool"
        and messages[-1]["tool_call_id"] == "call-query-1"
    )
    history = client.get(
        f"/api/sessions/{result['session_id']}/messages", headers=alice
    ).json()
    assert history[-1]["artifacts"] == result["artifacts"]
    assert (
        client.get(
            f"/api/sessions/{result['session_id']}/messages", headers=bob
        ).status_code
        == 404
    )
    before = len(requests)
    assert (
        client.post(
            "/api/chat/stream",
            headers=bob,
            json={"message": "越权", "session_id": result["session_id"]},
        ).status_code
        == 404
    )
    assert len(requests) == before
    second = decode(
        client.post(
            "/api/chat/stream",
            headers=alice,
            json={"message": "继续查询", "session_id": result["session_id"]},
        )
    )
    assert second[-1][0] == "done"
    assert "历史业务结果" in json.dumps(requests[2]["messages"], ensure_ascii=False)


def test_agent_corrects_rejected_sql_within_budget(agent_case):
    client, (alice, _), question, install, requests, _ = agent_case
    install(
        lambda _, index: (
            {"calls": [call("SELECT token_hash FROM access_tokens")]}
            if index == 1
            else {"calls": [call()]}
            if index == 2
            else {"text": "已查询自己的订单。"}
        )
    )
    result = decode(
        client.post("/api/chat/stream", headers=alice, json={"message": question})
    )[-1]
    assert result[0] == "done" and len(requests) == 3
    assert json.loads(requests[1]["messages"][-1]["content"])["status"] == "rejected"
    assert result[1]["artifacts"][0]["rows"] == [["DEMO-A001"]]


def test_draft_is_a_chat_tool_and_does_not_create_business_order(agent_case):
    client, (alice, _), question, install, requests, _ = agent_case
    description = "我的 DEMO-A001 耳机损坏，需要退货，数量1。"
    install(
        lambda _, index: (
            {
                "calls": [
                    call(
                        name="prepare_after_sales",
                        arguments={},
                    )
                ]
            }
            if index == 1
            else {"text": "资料已整理，尚未创建售后单。"}
        )
    )
    result = decode(
        client.post(
            "/api/chat/stream", headers=alice, json={"message": question + description}
        )
    )[-1]
    assert result[0] == "done" and result[1]["artifacts"], requests[-1]["messages"][-1]
    assert result[1]["artifacts"][0]["kind"] == "draft"
    assert result[1]["artifacts"][0]["draft"]["quantity"] == 1 and len(requests) == 3


@pytest.mark.parametrize(
    "failure", ["unknown", "bad_id", "length", "eof", "rate", "repeat"]
)
def test_agent_failure_is_safe_and_does_not_persist_half_turn(agent_case, failure):
    client, (alice, _), question, install, requests, _ = agent_case

    def script(_, index):
        if failure == "unknown":
            return {"calls": [call(name="delete_order")]}
        if failure == "bad_id":
            return {"calls": [call(id="")]}
        if failure == "repeat":
            return {"calls": [call()]}
        if index == 1:
            return {"calls": [call()]}
        if failure == "eof":
            return {"text": "部分正文", "finish": None}
        return (
            {"text": "不完整", "finish": "length"}
            if failure == "length"
            else {"status": 429}
        )

    install(script)
    response = client.post(
        "/api/chat/stream", headers=alice, json={"message": question}
    )
    events = decode(response)
    assert events[-1][0] == "error" and "private" not in response.text
    assert events[-1][1]["status"] in (502, 503)
    assert len(requests) <= 4
    assert question not in [
        row["title"] for row in client.get("/api/sessions", headers=alice).json()
    ]


def test_sync_chat_uses_same_agent(agent_case):
    client, (alice, _), question, install, _, _ = agent_case
    install(
        lambda _, index: (
            {"calls": [call()]} if index == 1 else {"text": "订单查询完成。"}
        )
    )
    response = client.post("/api/chat", headers=alice, json={"message": question})
    assert response.status_code == 200 and response.json()["artifacts"][0]["rows"] == [
        ["DEMO-A001"]
    ]


def test_agent_stream_cancellation_closes_model_and_does_not_save(agent_case):
    _, _, question, install, _, closed = agent_case
    install(
        lambda _, index: (
            {"calls": [call()]} if index == 1 else {"text": "部分回答", "hang": True}
        )
    )

    async def cancel():
        with SessionLocal() as db:
            owner = db.scalar(select(User.id).where(User.username == "alice"))
            prepared = chat.prepare_stream(db, owner, ChatInput(message=question))
        async with aclosing(chat.stream_message(prepared)) as stream:
            async for name, _ in stream:
                if name == "delta":
                    break
        await asyncio.sleep(0)

    with asyncio.Runner() as runner:
        runner.run(asyncio.wait_for(cancel(), timeout=10))
    assert closed
    with SessionLocal() as db:
        assert (
            db.scalar(select(ChatSession.id).where(ChatSession.title == question))
            is None
        )
