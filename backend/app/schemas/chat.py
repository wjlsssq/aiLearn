"""聊天与会话接口的数据契约。"""

from pydantic import BaseModel, Field  # DTO 类型和输入校验。


class ChatInput(BaseModel):  # 单次聊天请求 DTO。
    message: str = Field(min_length=1, max_length=2000)  # 防止无限大的消息入库。
    session_id: int | None = None  # 不传表示建立新会话。


class ChatResponse(BaseModel):  # 聊天接口响应。
    session_id: int  # 持久化会话 ID。
    reply: str  # 本次助手回复。
    mode: str  # 明确标注 mock 或 llm。
    model: str | None = None  # 真实调用时返回配置的模型名。


class SessionResponse(BaseModel):  # 左侧会话列表项。
    id: int  # 会话标识。
    title: str  # 展示标题。


class MessageResponse(BaseModel):  # 历史消息项。
    role: str  # 对话角色。
    content: str  # 对话内容。
