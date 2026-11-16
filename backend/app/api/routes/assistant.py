"""面向业务用户的只读订单助手，隐藏模型协议与内部执行轨迹。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import current_user
from ...db.session import get_db
from ...models import User
from ...schemas.tool_calling import OrderAssistantInput, OrderAssistantResponse
from ...services.assistant import query_order

router = APIRouter(prefix="/assistant", tags=["业务助手"])


@router.post("/orders", response_model=OrderAssistantResponse)
def order(
    body: OrderAssistantInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    user_id = user.id
    db.rollback()  # 等待模型时释放认证查询事务。
    return query_order(user_id, body)
