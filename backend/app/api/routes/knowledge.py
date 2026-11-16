"""Q07：认证后的私有教学知识库，不接收服务器文件路径。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import current_user
from ...db.session import get_db
from ...models import User
from ...schemas.knowledge import (
    KnowledgeInput,
    SplitPreview,
    ImportResult,
    KnowledgeVersion,
    DocumentSummary,
    VersionSummary,
)
from ...services import knowledge as service

router = APIRouter(prefix="/knowledge", tags=["服务文档"])


@router.post("/import", response_model=ImportResult)
def import_text(
    body: KnowledgeInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return service.import_document(db, user.id, body)


@router.get("/documents", response_model=list[DocumentSummary])
def documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return service.list_documents(db, user.id)


@router.get("/documents/{document_id}/versions", response_model=list[VersionSummary])
def versions(
    document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return service.list_versions(db, user.id, document_id)


@router.get("/documents/{document_id}", response_model=KnowledgeVersion)
def current(
    document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return service.read_version(db, user.id, document_id)


@router.get(
    "/documents/{document_id}/versions/{revision}", response_model=KnowledgeVersion
)
def version(
    document_id: int,
    revision: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return service.read_version(db, user.id, document_id, revision)
