"""Q02：组织不调用模型的 Prompt 预览。"""

from ..ai.prompts.customer_service import (
    PROMPT_ID,
    PROMPT_VERSION,
    build_chat_messages,
)  # 只使用统一的模板渲染入口。
from ..schemas.prompt import (
    PromptMessage,
    PromptPreviewInput,
    PromptPreviewResponse,
)  # 将 AI 层对象转换为稳定的接口 DTO。


def preview_prompt(body: PromptPreviewInput) -> PromptPreviewResponse:
    """返回完整消息和版本；不访问模型服务、不创建会话或写入业务数据。"""
    messages = build_chat_messages(
        body.message, store_name=body.store_name, style=body.style
    )  # 与网关使用相同变量和风格映射。
    return PromptPreviewResponse(
        template_id=PROMPT_ID,
        version=PROMPT_VERSION,
        messages=[
            PromptMessage(
                role="system" if message.type == "system" else "user",
                content=str(message.content),
            )
            for message in messages
        ],  # LangChain 的 human 在对外协议中对应 user。
    )
