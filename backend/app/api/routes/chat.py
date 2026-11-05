"""会话与聊天 HTTP 适配。"""

from fastapi import APIRouter, Depends  # 路由与依赖声明。
from fastapi.responses import StreamingResponse  # 使用 HTTP 流传递 SSE 事件。
from contextlib import aclosing  # 浏览器中断连接时关闭业务流。
import json  # JSON 转义确保正文换行不会破坏 SSE 帧。
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


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "start/delta/done/error 事件流",
        }
    },
)
def chat_stream(
    body: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    """保留普通聊天接口，新增支持 Bearer 认证和 POST 请求的 SSE 流。"""
    prepared = service.prepare_stream(
        db, user.id, body
    )  # 在发送 200 响应前拒绝越权与空白。

    async def events():
        async with aclosing(service.stream_message(prepared)) as stream:
            async for name, data in stream:
                yield f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )  # 反向代理也需要允许流直接通过，不能等待完整响应。
