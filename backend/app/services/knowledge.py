"""Q07：用户隔离、版本语义与导入事务；此课不检索、不生成回答。"""

import hashlib
import unicodedata
from pathlib import Path
from sqlalchemy.orm import Session
from ..ai.rag.splitter import preview_document
from ..core.errors import BusinessError
from ..repositories import knowledge as repository
from ..schemas.knowledge import (
    KnowledgeInput,
    KnowledgeVersion,
    ImportResult,
    DocumentSummary,
    VersionSummary,
    SplitOptions,
    ChunkPreview,
)


def example_document() -> KnowledgeInput:
    source = Path(__file__).resolve().parents[3] / "datasets" / "shop-rules-demo.md"
    return KnowledgeInput(title="合成售后规则", text=source.read_text(encoding="utf-8"))


def require_document(db: Session, user_id: int, document_id: int):
    document = repository.find_document(db, user_id, document_id)
    if document is None:
        raise BusinessError(404, "文档不存在")  # 不透露其他人的文档是否存在。
    return document


def list_documents(db: Session, user_id: int):
    return [
        DocumentSummary(id=d.id, title=d.title, active_revision=d.active_revision)
        for d in repository.list_documents(db, user_id)
    ]


def list_versions(db: Session, user_id: int, document_id: int):
    document = require_document(db, user_id, document_id)  # 授权先于版本查询。
    return [
        VersionSummary(
            revision=v.revision,
            active=v.revision == document.active_revision,
            content_hash=v.content_hash,
            chunk_count=v.chunk_count,
            options=SplitOptions(
                chunk_size=v.chunk_size, chunk_overlap=v.chunk_overlap
            ),
        )
        for v in repository.list_versions(db, document.id)
    ]


def read_version(
    db: Session, user_id: int, document_id: int, revision: int | None = None
) -> KnowledgeVersion:
    document = require_document(db, user_id, document_id)
    version = repository.find_version(
        db, document.id, document.active_revision if revision is None else revision
    )
    if version is None:
        raise BusinessError(404, "版本不存在")
    chunks = [
        ChunkPreview(
            ordinal=c.ordinal,
            text=c.content,
            start=c.start_offset,
            end=c.end_offset,
            start_line=c.start_line,
            end_line=c.end_line,
            heading=c.heading,
        )
        for c in repository.list_chunks(db, version.id)
    ]
    return KnowledgeVersion(
        document_id=document.id,
        title=document.title,
        revision=version.revision,
        active=version.revision == document.active_revision,
        normalized_text=version.content,
        content_hash=version.content_hash,
        fingerprint=version.fingerprint,
        splitter_version=version.splitter_version,
        options=SplitOptions(
            chunk_size=version.chunk_size, chunk_overlap=version.chunk_overlap
        ),
        chunks=chunks,
    )


def import_document(db: Session, user_id: int, body: KnowledgeInput) -> ImportResult:
    preview = preview_document(body)  # 先纯计算校验，失败不创建空文档。
    normalized_title = unicodedata.normalize("NFKC", preview.title).casefold()
    key = hashlib.sha256(
        normalized_title.encode()
    ).hexdigest()  # 同用户同标题视为同文档。
    db.rollback()  # 结束认证读取的旧快照；并发锁等待后要读取最新已提交版本。
    try:
        document = repository.lock_document(db, user_id, key, preview.title)
        active = repository.find_version(db, document.id, document.active_revision)
        reused = active is not None and active.fingerprint == preview.fingerprint
        if not reused:
            repository.add_version(db, document, preview)
        result = ImportResult(
            reused=reused, version=read_version(db, user_id, document.id)
        )
        db.commit()  # 原文、块、版本与有效指针一起提交，响应构造也在提交前完成。
        return result
    except Exception:
        db.rollback()  # 失败不留下半版本，更不提前失效旧版本。
        raise
