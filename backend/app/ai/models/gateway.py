"""Q01：业务层与模型之间的单次问答边界。"""

from dataclasses import dataclass  # 用小型不可变结果对象隔离模型返回结构。
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)  # 适配器底层的标准请求异常。
from ...core.config import settings  # 当前运行模式。
from ...core.errors import BusinessError  # 不向客户端泄露供应商原始错误。
from .factory import create_chat_model  # 供应商差异集中在工厂中。
from ..prompts.customer_service import (
    DEFAULT_STORE_NAME,
    PROMPT_VERSION,
    PromptStyle,
    build_chat_messages,
)  # 系统指令与消息角色由业务模板统一维护。


@dataclass(frozen=True)  # 结果创建后不再被业务层修改。
class ModelReply:
    text: str  # 可保存的正文。
    mode: str  # mock 或 llm，避免把模拟数据冒充真实调用。
    model: str | None = None  # 真实调用的配置模型名。
    prompt_version: str = (
        PROMPT_VERSION  # 显式模拟也返回渲染模板版本，不代表请求了模型。
    )


def generate_reply(
    content: str,
    *,
    store_name: str = DEFAULT_STORE_NAME,
    style: PromptStyle = "concise",
) -> ModelReply:  # 本课只接受当前问题，不读取历史或订单。
    messages = build_chat_messages(
        content, store_name=store_name, style=style
    )  # 模拟和真实模式共用模板；只有后者会发送网络请求。
    if settings.chat_mode == "mock":  # 明确配置模拟模式时才使用固定回复。
        return ModelReply(
            text=f"【模拟回复】已收到：{content}。在 .env 配置模型并设置 CHAT_MODE=llm 后，可学习真实 LangChain 调用。",
            mode="mock",
        )  # 保留无需凭据的联调能力。
    try:  # 将供应商网络错误转换为稳定业务错误。
        model = create_chat_model()  # 获得统一聊天接口，构造本身不发送聊天请求。
        result = model.invoke(messages)  # 核心调用：输入消息列表，得到 AIMessage。
    except (AuthenticationError, PermissionDeniedError):  # 处理无效凭据或权限不足。
        raise BusinessError(
            502, "模型认证失败，请检查 API Key 和模型访问权限"
        ) from None  # 不返回原始异常中的请求信息。
    except RateLimitError:  # 余额或限流问题需结合供应商控制台确认。
        raise BusinessError(
            503, "模型服务限流或额度不足，请稍后重试并检查服务账户"
        ) from None  # 保持失败，不降级成模拟回复。
    except APITimeoutError:  # 超时与网络连接失败分别反馈。
        raise BusinessError(
            504, "模型响应超时，请稍后重试"
        ) from None  # 服务端已配置单次请求超时。
    except APIConnectionError:  # DNS、代理或 TLS 等连接故障。
        raise BusinessError(
            502, "无法连接模型服务，请检查 API 地址和网络"
        ) from None  # 避免回显敏感地址细节。
    except (
        APIStatusError
    ) as error:  # 捕获其他供应商 HTTP 错误，例如模型名错误或参数不支持。
        if error.status_code == 402:  # DeepSeek 通过 402 表示账户余额不足。
            raise BusinessError(
                503, "模型账户余额不足，请检查 DeepSeek 服务账户"
            ) from None  # 与错误的模型参数区分。
        raise BusinessError(
            502, "模型服务拒绝请求，请检查模型名称、接口地址和参数兼容性"
        ) from None  # 原始响应不直接展示。
    text = result.text.strip()  # 统一提取文本，避免业务层遍历供应商的 choices 结构。
    if not text:  # 没有文本不能写成成功问答。
        raise BusinessError(
            502, "模型未返回有效文本，请检查模型能力或稍后重试"
        )  # 不保存空的助手消息。
    return ModelReply(
        text=text, mode="llm", model=settings.llm_model.strip()
    )  # 对外只暴露业务需要的字段。
