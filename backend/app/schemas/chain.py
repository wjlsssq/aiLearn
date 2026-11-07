"""Q03：实验输入与可序列化的步骤报告。"""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .prompt import PromptOptions, PromptMessage


class ChainInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # 此处不 strip，确保实验能观察 normalize 前后的真实差别。
    questions: list[Annotated[str, Field(min_length=1, max_length=2000)]] = Field(
        min_length=1, max_length=2
    )
    method: Literal["invoke", "batch"] = "invoke"
    prompt: PromptOptions

    @model_validator(mode="after")
    def check_count(self):
        expected = 1 if self.method == "invoke" else 2
        if len(self.questions) != expected:
            raise ValueError("invoke 需要一题，batch 需要两题")
        return self


class ChainStep(BaseModel):
    name: str
    status: Literal["done", "failed", "skipped"]
    input_type: str
    output_type: str | None = None
    # JSON 可直接显示空格与换行；不返回对象内部配置。
    output: str | None = None


class ChainResult(BaseModel):
    index: int
    original: str
    normalized: str | None = None
    messages: list[PromptMessage] = Field(default_factory=list)
    reply: str | None = None
    error: str | None = None
    failed_stage: str | None = None
    steps: list[ChainStep]


class ChainReport(BaseModel):
    execution: Literal["inspect", "invoke", "batch"]
    mode: str
    model: str | None = None
    prompt_version: str
    results: list[ChainResult]
