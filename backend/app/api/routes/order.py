"""订单 HTTP 适配。"""

from fastapi import APIRouter, Depends  # 路由与依赖声明。
from sqlalchemy.orm import Session  # 请求级数据库会话。
from ...db.session import get_db  # 注入数据库连接。
from ..dependencies import current_user  # 注入已认证用户。
from ...models import User  # 用户类型。
from ...schemas.order import OrderResponse  # 响应 DTO。
from ...services.order import list_orders  # 订单业务。

router = APIRouter(tags=["订单"])  # 业务分组。


@router.get("/orders", response_model=list[OrderResponse])  # 返回当前用户订单。
def orders(
    user: User = Depends(current_user), db: Session = Depends(get_db)
):  # 身份由后端认证。
    return list_orders(db, user.id)  # 不接受前端任意指定用户。
