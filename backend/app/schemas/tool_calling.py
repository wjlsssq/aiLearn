"""Q12：模型只提议工具参数，身份和执行预算始终由后端控制。"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .order import OrderResponse


class ToolExperimentInput(BaseModel):
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
    logistics: str | None = None  # 明确标注教学模拟，没有接入物流服务。


class ToolStep(BaseModel):
    stage: Literal["model", "tool"]
    label: str
    status: Literal["done", "failed", "blocked"]
    message: str
    call_id: str | None = None
    name: str | None = None
    arguments: dict[str, str] = Field(
        default_factory=dict
    )  # 仅展示校验后的白名单参数。
    result: OrderToolResult | None = None


class ToolExperimentReport(BaseModel):
    mode: Literal["mock", "llm"]
    status: Literal["complete", "blocked", "failed"]
    answer: str | None = None
    model_calls: int = 0  # 模拟模式不冒充真实请求。
    tool_executions: int = 0  # 只有通过白名单与参数校验才计入。
    steps: list[ToolStep] = Field(default_factory=list)


class OrderToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict
    max_tool_executions: int = 1
    max_model_calls: int = 2
