"""Q03：真实 LCEL 行为、请求边界与离线步骤追踪。"""

import time
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate

from backend.app.ai.chains.customer_service import build_chain, build_prefix, StepTrace
from backend.app.api.dependencies import current_user
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models import User
from backend.app.schemas.chain import ChainInput
from backend.app.services import chain as service
from backend.app.ai.chains import customer_service


def body(questions, method="invoke"):
    return ChainInput(
        questions=questions,
        method=method,
        prompt={"store_name": "实验店", "style": "concise"},
    )


def test_inspect_has_actual_types_and_preserves_literal_data(monkeypatch):
    def forbidden():
        raise AssertionError("预览不应创建模型")

    monkeypatch.setattr(service, "select_model", forbidden)
    result = service.run_experiment(
        body(['  A  B\r\n{"x":1}  ']), inspect=True
    ).results[0]
    assert result.normalized == 'A  B\n{"x":1}'
    assert result.messages[1].content == result.normalized
    assert [s.output_type for s in result.steps] == [
        "dict",
        "ChatPromptValue",
        None,
        None,
    ]
    assert [s.status for s in result.steps] == ["done", "done", "skipped", "skipped"]


def test_chain_invoke_trace_and_true_stream():
    model = FakeListChatModel(responses=["第一块第二块"])
    chain = build_chain(model)
    value = {"question": "问题", "store_name": "店", "style": "concise"}
    trace = StepTrace()
    assert chain.invoke(value, config={"callbacks": [trace]}) == "第一块第二块"
    assert isinstance(trace.outputs["model"], AIMessage)
    assert isinstance(
        trace.outputs["parse"], str
    )  # 当前版本可能返回 str 的 TextAccessor 子类。
    chunks = list(chain.stream(value))
    assert len(chunks) > 1 and "".join(chunks) == "第一块第二块"


class SelectiveModel(FakeMessagesListChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        question = messages[-1].text
        if question == "慢题":
            time.sleep(0.03)  # 先完成第二题，返回仍须按输入顺序。
        if question == "失败题":
            raise RuntimeError("private-token-must-never-leak")
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=question))]
        )


def test_batch_order_trace_isolation_and_independent_failure(monkeypatch):
    monkeypatch.setattr(
        service,
        "select_model",
        lambda: SelectiveModel(responses=[AIMessage(content="unused")]),
    )
    report = service.run_experiment(body(["慢题", "快题"], "batch"))
    assert [r.reply for r in report.results] == ["慢题", "快题"]
    assert [r.messages[1].content for r in report.results] == ["慢题", "快题"]
    report = service.run_experiment(body(["失败题", "快题"], "batch"))
    first, second = report.results
    assert first.failed_stage == "model" and first.reply is None
    assert first.steps[-1].status == "skipped" and second.reply == "快题"
    assert "private-token" not in report.model_dump_json()


def test_normalize_and_prompt_failures_are_located(monkeypatch):
    result = service.run_experiment(body([" \r\n "]), inspect=True).results[0]
    assert result.failed_stage == "normalize" and result.steps[1].status == "skipped"
    trace = StepTrace()
    # 缺少店铺变量在规范化阶段就会报错；替换风格映射值不能凭空补齐。
    with pytest.raises(KeyError):
        build_prefix().invoke(
            {"question": "问题", "style": "concise"}, config={"callbacks": [trace]}
        )
    assert trace.failed_stage == "normalize"
    monkeypatch.setattr(
        customer_service,
        "CUSTOMER_SERVICE_PROMPT",
        ChatPromptTemplate.from_messages([("human", "{missing}")]),
    )
    result = service.run_experiment(body(["问题"]), inspect=True).results[0]
    assert result.failed_stage == "prompt"
    assert [s.status for s in result.steps] == ["done", "failed", "skipped", "skipped"]


def test_empty_model_text_is_not_success(monkeypatch):
    monkeypatch.setattr(
        service, "select_model", lambda: FakeListChatModel(responses=["  "])
    )
    result = service.run_experiment(body(["问题"])).results[0]
    assert result.reply is None and result.failed_stage == "parse"
    assert result.steps[-1].status == "failed"


def test_chain_http_auth_and_validation(monkeypatch):
    with TestClient(app) as client:
        payload = body(["问题"]).model_dump()
        assert client.post("/api/chains/inspect", json=payload).status_code == 401
        assert client.post("/api/chains/run", json=payload).status_code == 401
        monkeypatch.setitem(
            app.dependency_overrides,
            current_user,
            lambda: User(id=1, username="chain-test", password_hash="unused"),
        )
        monkeypatch.setattr(settings, "chat_mode", "mock")
        assert client.post("/api/chains/inspect", json=payload).status_code == 200
        assert (
            client.post("/api/chains/run", json=payload)
            .json()["results"][0]["reply"]
            .startswith("【模拟")
        )
        payload["questions"] = ["第一题", "第二题"]
        assert client.post("/api/chains/run", json=payload).status_code == 422
        payload["method"] = "batch"
        assert len(client.post("/api/chains/run", json=payload).json()["results"]) == 2
        payload["questions"] = ["a" * 2001, "第二题"]
        assert client.post("/api/chains/run", json=payload).status_code == 422
