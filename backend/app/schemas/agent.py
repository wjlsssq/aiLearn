"""聊天工具输入与业务结果；身份不属于模型可填写的参数。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .draft import AfterSalesDraft


class OrderQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sql: str = Field(min_length=1, max_length=2000)


class PrepareAfterSalesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QueryResult(BaseModel):
    status: Literal["ok", "rejected", "unavailable"]
    message: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str | int | float | None]] = Field(default_factory=list)
    truncated: bool = False


class ChatArtifact(BaseModel):
    kind: Literal["orders", "draft"]
    title: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str | int | float | None]] = Field(default_factory=list)
    truncated: bool = False
    draft: AfterSalesDraft | None = None
    missing_fields: list[str] = Field(default_factory=list)
