"""Q02：Prompt 配置与预览的数据契约。"""

from typing import Literal  # 限定可选风格和消息角色。
from pydantic import BaseModel, ConfigDict, Field, field_validator  # 校验业务变量。


class PromptOptions(BaseModel):
    """显式传配置时必须填写店铺名称；客户端不能修改系统模板。"""

    model_config = ConfigDict(
        str_strip_whitespace=True, extra="forbid"
    )  # 拒绝未约定字段。
    store_name: str = Field(min_length=1, max_length=60)  # 必填业务变量，先去首尾空格。
    style: Literal["concise", "detailed"] = "concise"  # 默认简洁，可显式切换详细。

    @field_validator("store_name")
    @classmethod
    def single_line_store_name(cls, value: str) -> str:
        """店铺名仅使用单行标签；这项格式校验不构成模型权限控制。"""
        if "\n" in value or "\r" in value:  # 避免把多行文本误当业务名称。
            raise ValueError("店铺名称不能换行")  # FastAPI 将其映射为字段校验失败。
        return value  # 返回通过校验的字段值。


class PromptPreviewInput(PromptOptions):
    message: str = Field(
        min_length=1, max_length=2000
    )  # 与聊天保持相同的问题长度上限。


class PromptMessage(BaseModel):
    role: Literal["system", "user"]  # 本课只渲染两种角色，不伪造工具结果。
    content: str  # 完整渲染内容，以纯文本展示。


class PromptPreviewResponse(BaseModel):
    template_id: str  # 由后端决定的模板标识。
    version: str  # 对照实验使用的模板版本。
    messages: list[PromptMessage]  # 与真实调用共享渲染逻辑的消息列表。
