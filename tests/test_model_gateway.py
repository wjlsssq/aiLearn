"""Q01：使用真实适配器和本机内存 HTTP 响应验证模型契约，不调用付费服务。"""

import json  # 解析适配器实际发出的 HTTP 请求体。
import asyncio  # 无需额外插件即可执行异步模型流验证。
import httpx  # 用 MockTransport 替代外部网络。
import pytest  # 参数化供应商和故障场景。
from pydantic import SecretStr  # 测试凭据也保持脱敏展示。
from backend.app.ai.models import factory, gateway  # 本课模型工厂与调用边界。
from backend.app.core.config import settings  # 通过 monkeypatch 临时隔离本机设置。
from backend.app.core.errors import BusinessError  # 验证稳定的错误语义。


@pytest.fixture
def model_config(monkeypatch):  # 每个测试结束后自动恢复用户的真实配置。
    monkeypatch.setenv("LANGSMITH_TRACING", "false")  # 不把测试消息发送到外部追踪服务。
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")  # 同时隔离旧名称的追踪开关。
    monkeypatch.setattr(settings, "chat_mode", "llm")  # 明确测试真实适配器分支。
    monkeypatch.setattr(
        settings, "llm_provider", "openai_compatible"
    )  # 默认标准兼容协议。
    monkeypatch.setattr(
        settings, "llm_base_url", "https://model.test/v1"
    )  # 内存传输，不访问此地址。
    monkeypatch.setattr(settings, "llm_model", "test-chat-model")  # 测试模型标识。
    monkeypatch.setattr(
        settings, "llm_api_key", SecretStr("test-only-key")
    )  # 非真实凭据。


def completion(
    content: str = "你好，我可以帮助整理售后问题。",
) -> dict:  # 构造供应商标准响应。
    return {  # 使用真实协议结构验证 LangChain 的解析。
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-chat-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
    }


def install_transport(
    monkeypatch, handler
):  # 只替换 HTTP 传输，保留真实 LangChain / SDK 序列化。
    adapter = (
        factory.ChatDeepSeek
        if settings.llm_provider == "deepseek"
        else factory.ChatOpenAI
    )  # 取得真实适配器类。
    name = (
        "ChatDeepSeek" if settings.llm_provider == "deepseek" else "ChatOpenAI"
    )  # 工厂当前使用的构造入口。
    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )  # 所有请求在进程内响应。
    monkeypatch.setattr(
        factory, name, lambda **options: adapter(**options, http_client=client)
    )  # 在原参数基础上注入传输。
    return client  # 测试使用 with 保证关闭连接资源。


@pytest.mark.parametrize("provider", ["openai_compatible", "deepseek"])
def test_real_adapters_use_current_question_only(
    model_config, monkeypatch, provider
):  # 两种适配器都遵循本课消息契约。
    monkeypatch.setattr(settings, "llm_provider", provider)  # 选择待验证供应商分支。
    requests = []  # 记录实际 HTTP 请求，检查次数与内容。

    def handle(request):  # 供应商协议在内存中接收请求。
        requests.append(json.loads(request.content))  # 保存模型看到的消息列表。
        return httpx.Response(200, json=completion())  # 返回标准聊天结果。

    with install_transport(monkeypatch, handle):  # 不触发任何外部模型服务。
        reply = gateway.generate_reply("你能帮我做什么？")  # 执行真实模型适配器逻辑。
    assert (
        reply.mode == "llm" and reply.model == "test-chat-model"
    )  # 不能把成功结果标为模拟。
    assert reply.text == "你好，我可以帮助整理售后问题。"  # 统一得到可持久化文本。
    assert len(requests) == 1  # Q01 显式关闭自动重试。
    assert requests[0]["model"] == "test-chat-model"  # 配置正确传给供应商。
    if provider == "deepseek":  # 专用适配器保留供应商扩展参数。
        assert requests[0]["thinking"] == {
            "type": "disabled"
        }  # 本课使用非思考文本模式。
    assert [message["role"] for message in requests[0]["messages"]] == [
        "system",
        "user",
    ]  # 不包含历史或订单。
    assert (
        requests[0]["messages"][-1]["content"] == "你能帮我做什么？"
    )  # 当前问题完整传入。


@pytest.mark.parametrize(
    "status, expected",
    [(401, 502), (402, 503), (403, 502), (429, 503), (404, 502), (500, 502)],
)
def test_provider_failure_is_safe_and_never_mock(
    model_config, monkeypatch, status, expected
):  # 失败不伪装成成功。
    calls = []  # 确认故障不会触发隐式重试。

    def handle(request):  # 模拟供应商失败。
        calls.append(request)  # 记录请求次数。
        return httpx.Response(
            status,
            json={
                "error": {
                    "message": "private-provider-detail test-only-key",
                    "type": "provider_error",
                }
            },
        )  # 故意加入应隐藏的信息。

    with (
        install_transport(monkeypatch, handle),
        pytest.raises(BusinessError) as caught,
    ):  # 预期进入统一错误边界。
        gateway.generate_reply("测试失败")  # 不返回模拟回复。
    assert caught.value.status_code == expected  # 前端得到可识别的错误状态。
    assert (
        "test-only-key" not in caught.value.message
        and "private-provider-detail" not in caught.value.message
    )  # 原始响应不泄露。
    assert len(calls) == 1  # 失败只执行一次请求。


def test_timeout_has_distinct_error(
    model_config, monkeypatch
):  # 区分供应商超时与其他错误。
    def handle(request):  # 内存中模拟网络读取超时。
        raise httpx.ReadTimeout(
            "private-network-detail", request=request
        )  # 由真实 SDK 转换异常。

    with (
        install_transport(monkeypatch, handle),
        pytest.raises(BusinessError) as caught,
    ):  # 验证异常映射。
        gateway.generate_reply("测试超时")  # 不等待真实网络。
    assert caught.value.status_code == 504  # 网关超时有独立状态。


def test_empty_text_is_not_success(
    model_config, monkeypatch
):  # 空响应不能形成有效聊天记录。
    with (
        install_transport(
            monkeypatch, lambda request: httpx.Response(200, json=completion("   "))
        ),
        pytest.raises(BusinessError) as caught,
    ):  # 返回合法协议但无效文本。
        gateway.generate_reply("测试空回复")  # 进入文本校验。
    assert caught.value.status_code == 502  # 不把空回复作为成功结果。


def test_missing_key_is_rejected_before_network(
    model_config, monkeypatch
):  # 配置缺失时停止调用。
    monkeypatch.setattr(settings, "llm_api_key", SecretStr(""))  # 模拟未填密钥。
    with pytest.raises(BusinessError) as caught:  # 工厂不创建网络请求。
        gateway.generate_reply("测试配置")  # 请求在配置检查阶段失败。
    assert caught.value.status_code == 503  # 模型尚未准备好。


@pytest.mark.parametrize("provider", ["openai_compatible", "deepseek"])
@pytest.mark.parametrize("style", ["concise", "detailed"])
def test_prompt_preview_matches_actual_model_messages(
    model_config, monkeypatch, provider, style
):
    """预览必须等于真实适配器发出的消息，而非只测试两个函数各自能运行。"""
    from backend.app.schemas.prompt import PromptPreviewInput  # 本课真实请求 DTO。
    from backend.app.services.prompt import preview_prompt  # 本课预览服务。

    monkeypatch.setattr(settings, "llm_provider", provider)  # 覆盖两种协议适配器。
    requests = []  # 接收内存 HTTP 请求体。

    def handle(request):
        requests.append(json.loads(request.content))  # 观察序列化之后的实际消息。
        return httpx.Response(200, json=completion())

    body = PromptPreviewInput(
        message="问题里有 {unknown}", store_name="对照店", style=style
    )
    preview = preview_prompt(body)  # 不请求供应商、不创建业务记录。
    with install_transport(monkeypatch, handle):
        reply = gateway.generate_reply(
            body.message, store_name=body.store_name, style=body.style
        )
    assert len(requests) == 1  # 只有网关发起一次内存请求。
    assert requests[0]["messages"] == [
        message.model_dump() for message in preview.messages
    ]
    assert reply.prompt_version == preview.version  # 版本与发送内容一起对齐。


@pytest.mark.parametrize("provider", ["openai_compatible", "deepseek"])
def test_real_async_adapters_stream_deltas(model_config, monkeypatch, provider):
    monkeypatch.setattr(settings, "llm_provider", provider)
    adapter = factory.ChatDeepSeek if provider == "deepseek" else factory.ChatOpenAI
    requests = []
    frames = []
    for delta, finish in [
        ({"role": "assistant", "content": "你好"}, None),
        ({"content": " "}, None),
        ({"content": "世界\n"}, None),
        ({}, "stop"),
    ]:
        frames.append(
            "data: "
            + json.dumps(
                {
                    "id": "stream-test",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": "test-chat-model",
                    "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
                }
            )
            + "\n\n"
        )
    payload = "".join(frames) + "data: [DONE]\n\n"

    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=payload.encode()
        )

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            name = "ChatDeepSeek" if provider == "deepseek" else "ChatOpenAI"
            monkeypatch.setattr(
                factory,
                name,
                lambda **options: adapter(**options, http_async_client=client),
            )
            return [
                text
                async for text in gateway.stream_reply(
                    "流式问题", store_name="流式店", style="detailed"
                )
            ]

    assert asyncio.run(collect()) == [
        "你好",
        " ",
        "世界\n",
    ]  # 空格不能因逐块 strip 丢失。
    assert len(requests) == 1 and requests[0]["stream"] is True
    assert requests[0]["messages"][-1]["content"] == "流式问题"


def test_async_stream_timeout_is_safe(model_config, monkeypatch):
    async def handle(request):
        raise httpx.ReadTimeout("private-stream-detail", request=request)

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            adapter = factory.ChatOpenAI
            monkeypatch.setattr(
                factory,
                "ChatOpenAI",
                lambda **options: adapter(**options, http_async_client=client),
            )
            return [text async for text in gateway.stream_reply("流式超时")]

    with pytest.raises(BusinessError) as caught:
        asyncio.run(collect())
    assert caught.value.status_code == 504
    assert "private-stream-detail" not in caught.value.message


@pytest.mark.parametrize("broken_read", [False, True])
def test_truncated_model_stream_is_not_success(model_config, monkeypatch, broken_read):
    class TruncatedStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            chunk = {
                "id": "cut",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "test-chat-model",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "只有前半段"},
                        "finish_reason": None,
                    }
                ],
            }
            yield ("data: " + json.dumps(chunk) + "\n\n").encode()
            if broken_read:
                raise httpx.ReadError(
                    "private-stream-reset"
                )  # 另一分支模拟干净 EOF 但缺结束标记。

    async def handle(request):
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=TruncatedStream()
        )

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            adapter = factory.ChatOpenAI
            monkeypatch.setattr(
                factory,
                "ChatOpenAI",
                lambda **options: adapter(**options, http_async_client=client),
            )
            return [text async for text in gateway.stream_reply("截断测试")]

    with pytest.raises(BusinessError) as caught:
        asyncio.run(collect())
    assert caught.value.status_code == 502
    assert "private-stream-reset" not in caught.value.message
