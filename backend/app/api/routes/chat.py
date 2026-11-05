"""会话与聊天 HTTP 适配。"""

from fastapi import APIRouter, Depends  # 路由与依赖声明。
from sqlalchemy.orm import Session  # 请求级数据库会话。
from ...db.session import get_db  # 注入数据库连接。
from ..dependencies import current_user  # 当前登录身份。
from ...models import User  # 用户类型。
from ...schemas.chat import (
    ChatInput,
    ChatResponse,
    SessionResponse,
    MessageResponse,
)  # 请求响应 DTO。
from ...services import chat as service  # 聊天业务入口。

router = APIRouter(tags=["聊天"])  # 会话与消息 API 分组。


@router.get("/sessions", response_model=list[SessionResponse])  # 当前用户会话摘要。
def sessions(
    user: User = Depends(current_user), db: Session = Depends(get_db)
):  # 后端身份和数据库依赖。
    return service.list_sessions(db, user.id)  # 交给 Service 组织输出。


@router.get(
    "/sessions/{session_id}/messages", response_model=list[MessageResponse]
)  # 读取持久化历史。
def messages(
    session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):  # 绑定路径参数。
    return service.list_messages(db, session_id, user.id)  # Service 先校验归属。


@router.post("/chat", response_model=ChatResponse)  # 模拟聊天接口保持兼容。
def chat(
    body: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):  # 验证请求 DTO。
    return service.send_message(db, user.id, body)  # Service 管理整个写入事务。
