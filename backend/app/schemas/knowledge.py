"""Q07：纯文本切分、预览与版本导入契约。"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SplitOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    chunk_size: int = Field(default=300, ge=64, le=2000)  # Python 字符数，不是 token。
    chunk_overlap: int = Field(
        default=60, ge=0, le=1000
    )  # 目标重叠量，不保证每对都达到。

    @model_validator(mode="after")
    def valid_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("重叠量必须小于块大小")
        return self


class KnowledgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=80, pattern=r"\S")
    text: str = Field(min_length=1, max_length=20000, pattern=r"\S")
    options: SplitOptions = Field(default_factory=SplitOptions)


class ChunkPreview(BaseModel):
    ordinal: int  # 从 1 开始的块序号。
    text: str
    start: int  # 规范化原文中的 Python Unicode 码点偏移，左闭右开。
    end: int
    start_line: int  # 从 1 开始，仅作阅读定位。
    end_line: int
    heading: str | None  # 块起点前最近的 Markdown 标题；不是完整层级解析。


class SplitPreview(BaseModel):
    title: str
    normalized_text: str  # BOM / 换行规范化后的唯一定位基准。
    content_hash: str
    fingerprint: str  # 原文与切分参数、算法版本的组合摘要。
    splitter_version: str
    options: SplitOptions
    chunks: list[ChunkPreview]


class KnowledgeVersion(SplitPreview):
    document_id: int
    revision: int
    active: bool


class ImportResult(BaseModel):
    reused: bool  # 仅当前有效版本指纹相同才复用。
    version: KnowledgeVersion


class DocumentSummary(BaseModel):
    id: int
    title: str
    active_revision: int


class VersionSummary(BaseModel):
    revision: int
    active: bool
    content_hash: str
    chunk_count: int
    options: SplitOptions
