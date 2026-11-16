"""订单助手请求、白名单工具参数与业务结果。"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .order import OrderResponse


class OrderAssistantInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)


class OrderLookupArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    order_no: str = Field(
        min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9-]*$"
    )
    # 不接受 user_id、SQL、路径或可执行代码；额外字段直接拒绝。


class OrderToolResult(BaseModel):
    status: Literal["found", "not_found", "invalid_arguments", "unknown_tool", "error"]
    message: str
    order: OrderResponse | None = None  # 只来自经过归属限定的 MySQL 查询。


class OrderAssistantResponse(BaseModel):
    status: Literal["complete", "blocked", "failed"]
    answer: str | None = None
    order: OrderResponse | None = None
    message: str  # 对业务用户只暴露结果，不返回工具 schema、协议或执行轨迹。
