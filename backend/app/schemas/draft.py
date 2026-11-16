"""Q06：输入 DTO、模型提取 schema 与页面报告，草稿不代表已授权工单。"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    description: str = Field(
        min_length=1, max_length=2000
    )  # 只提取本次描述，不读会话。


class AfterSalesDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True
    )  # 拒绝额外字段与隐式类型转换。
    order_no: str | None = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,39}$"
    )  # 未提供必须 null。
    issue_type: Literal["return", "exchange", "refund", "other", "unknown"]
    reason: str | None = Field(min_length=1, max_length=500)  # 只概括原文，不补编事实。
    quantity: int | None = Field(ge=1, le=99)  # 字符串数字和布尔值不当作数量。


class DraftReport(BaseModel):
    mode: Literal["mock", "llm"]  # 模拟样例必须明确标识。
    schema_version: str = "1.0.0"
    valid: bool  # 结构与本课的订单号来源检查是否通过，不代表订单真实或可售后。
    draft: AfterSalesDraft | None = None
    issues: list[str] = Field(
        default_factory=list
    )  # 仅返回安全字段提示，无供应商原始正文。
    missing_fields: list[str] = Field(
        default_factory=list
    )  # 服务端根据校验后结果计算。
