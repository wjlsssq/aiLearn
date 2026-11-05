"""Q01：将供应商配置集中映射成 LangChain 的统一聊天模型。"""

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)  # 上层依赖统一接口。
from langchain_openai import ChatOpenAI  # 标准 OpenAI 聊天协议适配器。
from langchain_deepseek import ChatDeepSeek  # 保留 DeepSeek 的供应商协议处理。
from ...core.config import Settings, settings  # 读取服务端配置。
from ...core.errors import BusinessError  # 输出安全的配置错误。


def is_model_configured(
    config: Settings = settings,
) -> bool:  # 仅判断必需字段，不发送网络请求。
    return bool(
        config.llm_base_url.strip()
        and config.llm_model.strip()
        and config.llm_api_key.get_secret_value().strip()
    )  # 不代表凭据已通过供应商验证。


def create_chat_model(
    config: Settings = settings,
) -> BaseChatModel:  # 工厂返回统一的模型类型。
    if not is_model_configured(config):  # 提前拦截缺失配置，避免发送无意义请求。
        raise BusinessError(
            503, "请先在本机 .env 配置 LLM_BASE_URL、LLM_MODEL 和 LLM_API_KEY"
        )  # 不回显配置或密钥。
    options = {  # 两个适配器共享的基础调用参数。
        "model": config.llm_model.strip(),  # API 中的模型标识。
        "base_url": config.llm_base_url.strip(),  # 供应商基础地址。
        "api_key": config.llm_api_key.get_secret_value(),  # 仅在构造后端客户端时读取明文。
        "temperature": config.llm_temperature,  # 本课只演示基本文本生成。
        "timeout": config.llm_timeout_seconds,  # 网络超时由业务错误映射处理。
        "max_retries": 0,  # Q01 不隐藏自动重试，便于观察一次调用的真实结果。
        "max_tokens": config.llm_max_tokens,  # 适配器负责供应商的参数序列化。
    }
    if config.llm_provider == "deepseek":  # DeepSeek 使用专用适配器。
        return ChatDeepSeek(
            **options, extra_body={"thinking": {"type": "disabled"}}
        )  # Q01 关闭 DeepSeek 思考模式，聚焦基础文本输入输出；对外仍为 BaseChatModel。
    return ChatOpenAI(
        **options, use_responses_api=False
    )  # 本课使用 Chat Completions 基础文本协议。
