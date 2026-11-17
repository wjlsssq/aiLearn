"""受认证保护的 Excel 快照下载，不暴露磁盘目录或公开链接。"""

from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import User
from ...services.order_export import download_export
from ..dependencies import current_user

router = APIRouter(tags=["订单导出"])


@router.get("/order-exports/{export_id}/download")
def download(
    export_id: UUID,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    filename, payload = download_export(db, user.id, export_id)
    return Response(
        payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
