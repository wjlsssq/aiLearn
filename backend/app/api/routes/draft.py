"""受认证保护的草稿提取接口；没有确认、建单或其他写操作。"""

from fastapi import APIRouter, Depends
from ..dependencies import current_user
from ...models import User
from ...schemas.draft import DraftInput, DraftReport
from ...services.draft import make_draft

router = APIRouter(prefix="/drafts", tags=["结构化售后草稿"])


@router.post("/extract", response_model=DraftReport)
def extract(body: DraftInput, user: User = Depends(current_user)):
    return make_draft(body)  # 身份只来自认证，不从模型字段取得。
