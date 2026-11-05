"""健康检查接口响应。"""

from pydantic import BaseModel  # 响应数据校验。


class HealthResponse(BaseModel):  # 页面展示的健康状态。
    status: str  # 探针状态。
    database: str  # 数据库类型。
    chat_mode: str  # 当前聊天模式。
    model_name: str | None = None  # 只展示模型标识，不展示密钥或 API 地址。
    model_configured: bool = True  # 本地配置齐全，不代表已验证供应商可用。
