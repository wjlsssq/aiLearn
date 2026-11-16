"""Q06：真实适配器的内存 HTTP 协议、严格校验与认证，不访问付费服务。"""

import json
import httpx
import pytest
from pydantic import SecretStr
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.dependencies import current_user
from backend.app.models import User
from backend.app.core.config import settings
from backend.app.core.errors import BusinessError
from backend.app.ai.models import factory
from backend.app.schemas.draft import DraftInput
from backend.app.services import draft as service

GOOD = {
    "order_no": "DEMO-A001",
    "issue_type": "exchange",
    "reason": "左耳无声",
    "quantity": 1,
}
DESCRIPTION = "订单 DEMO-A001，耳机左耳无声，我想换货，1 件。"


def install(monkeypatch, provider, content, finish="stop", status=200):
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    for key, value in dict(
        chat_mode="llm",
        llm_provider=provider,
        llm_base_url="https://model.test/v1",
        llm_model="test-model",
        llm_api_key=SecretStr("test-only-key"),
    ).items():
        monkeypatch.setattr(settings, key, value)
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        payload = {
            "id": "draft-test",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish,
                }
            ],
        }
        return httpx.Response(
            status,
            json=payload
            if status == 200
            else {"error": {"message": "private test-only-key"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handle))
    name = "ChatDeepSeek" if provider == "deepseek" else "ChatOpenAI"
    adapter = getattr(factory, name)
    monkeypatch.setattr(
        factory, name, lambda **options: adapter(**options, http_client=client)
    )
    return client, requests


@pytest.mark.parametrize("provider", ["deepseek", "openai_compatible"])
def test_real_json_mode_adapter_and_schema(monkeypatch, provider):
    client, requests = install(monkeypatch, provider, json.dumps(GOOD))
    with client:
        report = service.make_draft(DraftInput(description=DESCRIPTION))
    assert report.valid and report.draft.quantity == 1 and report.missing_fields == []
    assert len(requests) == 1 and requests[0]["response_format"] == {
        "type": "json_object"
    }
    assert requests[0]["messages"][-1]["content"] == DESCRIPTION
    assert "JSON" in requests[0]["messages"][0]["content"]


@pytest.mark.parametrize(
    "content",
    [
        "private test-only-key invalid JSON",
        json.dumps({k: v for k, v in GOOD.items() if k != "order_no"}),
        json.dumps({**GOOD, "issue_type": "delete_order"}),
        json.dumps({**GOOD, "quantity": "1"}),
        json.dumps({**GOOD, "quantity": True}),
        json.dumps({**GOOD, "quantity": -1}),
        json.dumps({**GOOD, "quantity": 100}),
        json.dumps({**GOOD, "admin": True}),
        json.dumps({**GOOD, "order_no": "invented-order"}),
    ],
)
def test_invalid_output_never_exposes_raw_or_creates_usable_draft(monkeypatch, content):
    client, _ = install(monkeypatch, "deepseek", content)
    with client:
        report = service.make_draft(DraftInput(description=DESCRIPTION))
    assert not report.valid and report.draft is None
    assert (
        "private" not in report.model_dump_json()
        and "test-only-key" not in report.model_dump_json()
    )


def test_explicit_nulls_trigger_server_clarification(monkeypatch):
    data = {"order_no": None, "issue_type": "unknown", "reason": None, "quantity": None}
    client, _ = install(monkeypatch, "deepseek", json.dumps(data))
    with client:
        report = service.make_draft(DraftInput(description="想咨询售后"))
    assert report.valid and set(report.missing_fields) == set(data)


@pytest.mark.parametrize(
    "finish,status",
    [("length", 200), ("content_filter", 200), ("stop", 401), ("stop", 429)],
)
def test_truncation_and_provider_failure_stay_errors(monkeypatch, finish, status):
    client, requests = install(
        monkeypatch, "deepseek", json.dumps(GOOD), finish, status
    )
    with client, pytest.raises(BusinessError):
        service.make_draft(DraftInput(description=DESCRIPTION))
    assert len(requests) == 1  # 不隐式重试或发第二次修复请求。


def test_http_auth_input_validation_and_mock(monkeypatch):
    monkeypatch.setattr(settings, "chat_mode", "mock")
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/drafts/extract", json={"description": DESCRIPTION}
            ).status_code
            == 401
        )
        monkeypatch.setitem(
            app.dependency_overrides,
            current_user,
            lambda: User(id=1, username="draft-test", password_hash="unused"),
        )
        for description in (" ", "a" * 2001):
            assert (
                client.post(
                    "/api/drafts/extract", json={"description": description}
                ).status_code
                == 422
            )
        response = client.post("/api/drafts/extract", json={"description": DESCRIPTION})
        assert response.status_code == 503
