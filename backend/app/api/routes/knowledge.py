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

router = APIRouter(prefix="/knowledge", tags=["文档切分与版本"])


@router.get("/example", response_model=KnowledgeInput)
def example(user: User = Depends(current_user)):
    return service.example_document()  # 固定合成样例，不读取用户指定的本机路径。


@router.post("/preview", response_model=SplitPreview)
def preview(body: KnowledgeInput, user: User = Depends(current_user)):
    return service.preview_document(body)  # 不写数据库，不调用模型。


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
