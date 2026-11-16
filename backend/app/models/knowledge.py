"""知识原文、不可变版本和分块；所有文档归属认证用户。"""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("user_id", "document_key", name="uq_knowledge_owner_key"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    document_key: Mapped[str] = mapped_column(
        String(64)
    )  # 规范化标题摘要，供重复导入定位。
    title: Mapped[str] = mapped_column(String(80))
    active_revision: Mapped[int] = mapped_column(
        default=0
    )  # 每个文档只有一个当前有效版本。


class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "revision", name="uq_knowledge_revision"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"))
    revision: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(
        MEDIUMTEXT
    )  # 20k 中文码点可能超过普通 TEXT 字节上限。
    content_hash: Mapped[str] = mapped_column(String(64))
    fingerprint: Mapped[str] = mapped_column(String(64))
    splitter_version: Mapped[str] = mapped_column(String(64))
    chunk_size: Mapped[int] = mapped_column()
    chunk_overlap: Mapped[int] = mapped_column()
    chunk_count: Mapped[int] = mapped_column()


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("version_id", "ordinal", name="uq_knowledge_chunk"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_document_versions.id")
    )
    ordinal: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int] = mapped_column()
    end_offset: Mapped[int] = mapped_column()
    start_line: Mapped[int] = mapped_column()
    end_line: Mapped[int] = mapped_column()
    heading: Mapped[str | None] = mapped_column(String(2000))
