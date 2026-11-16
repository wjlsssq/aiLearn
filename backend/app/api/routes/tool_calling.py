"""Q12：认证保护的订单工具实验。普通流式聊天暂不自动调用工具。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import current_user
from ...db.session import get_db
from ...models import User
from ...schemas.tool_calling import (
    ToolExperimentInput,
    ToolExperimentReport,
    OrderToolDefinition,
)
from ...services.tool_calling import run_order_tool, order_tool_definition

router = APIRouter(prefix="/tool-calling", tags=["订单工具实验"])


@router.get("/schema", response_model=OrderToolDefinition)
def schema(user: User = Depends(current_user)):
    return order_tool_definition()  # 只看公开 schema，不包含认证身份或数据库配置。


@router.post("/run", response_model=ToolExperimentReport)
def run(
    body: ToolExperimentInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    user_id = user.id  # 先取认证身份，释放会话后不依赖 ORM 实体。
    db.rollback()  # 模型请求期间释放认证读取连接。
    return run_order_tool(user_id, body)
