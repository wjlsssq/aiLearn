"""知识数据访问；无 HTTP 语义，不决定事务提交。"""

from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session
from ..models import (
    KnowledgeDocument as Document,
    KnowledgeDocumentVersion as Version,
    KnowledgeChunk,
)
from ..schemas.knowledge import SplitPreview


def lock_document(db: Session, user_id: int, key: str, title: str) -> Document:
    statement = insert(Document).values(
        user_id=user_id, document_key=key, title=title, active_revision=0
    )
    db.execute(
        statement.on_duplicate_key_update(id=Document.id)
    )  # 唯一键使首次并发导入也串行化。
    return db.scalar(
        select(Document)
        .where(Document.user_id == user_id, Document.document_key == key)
        .with_for_update()
    )


def find_document(db: Session, user_id: int, document_id: int) -> Document | None:
    return db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )


def list_documents(db: Session, user_id: int):
    return list(
        db.scalars(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.id.desc())
        )
    )


def list_versions(db: Session, document_id: int):
    return list(
        db.scalars(
            select(Version)
            .where(Version.document_id == document_id)
            .order_by(Version.revision.desc())
        )
    )


def find_version(db: Session, document_id: int, revision: int):
    return db.scalar(
        select(Version).where(
            Version.document_id == document_id, Version.revision == revision
        )
    )


def list_chunks(db: Session, version_id: int):
    return list(
        db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.version_id == version_id)
            .order_by(KnowledgeChunk.ordinal)
        )
    )


def add_version(db: Session, document: Document, preview: SplitPreview) -> Version:
    last = (
        db.scalar(
            select(func.max(Version.revision)).where(Version.document_id == document.id)
        )
        or 0
    )
    version = Version(
        document_id=document.id,
        revision=last + 1,
        content=preview.normalized_text,
        content_hash=preview.content_hash,
        fingerprint=preview.fingerprint,
        splitter_version=preview.splitter_version,
        chunk_size=preview.options.chunk_size,
        chunk_overlap=preview.options.chunk_overlap,
        chunk_count=len(preview.chunks),
    )
    db.add(version)
    db.flush()  # 获得版本 ID，后续写块仍未提交。
    db.add_all(
        [
            KnowledgeChunk(
                version_id=version.id,
                ordinal=chunk.ordinal,
                content=chunk.text,
                start_offset=chunk.start,
                end_offset=chunk.end,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                heading=chunk.heading,
            )
            for chunk in preview.chunks
        ]
    )
    document.active_revision = version.revision  # 新版本和有效指针在同一事务中切换。
    db.flush()
    return version
