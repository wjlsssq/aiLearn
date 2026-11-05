"""会话归属、消息校验和问答事务。"""

from sqlalchemy.orm import Session  # 当前业务事务。
from ..ai.models.gateway import generate_reply  # 模型调用细节封装在 AI 集成层。
from ..core.errors import BusinessError  # 与框架解耦的业务错误。
from ..models import ChatSession  # 标注已授权会话类型。
from ..repositories import chat as repository  # SQL 均由 Repository 执行。
from ..schemas.chat import (
    ChatInput,
    ChatResponse,
    SessionResponse,
    MessageResponse,
)  # 聊天请求契约。


def require_session(
    db: Session, session_id: int, user_id: int
) -> ChatSession:  # 统一执行会话所有权检查。
    session = repository.find_session(db, session_id, user_id)  # 数据库筛选 ID 与归属。
    if session is None:  # 不暴露其他用户会话是否存在。
        raise BusinessError(404, "会话不存在")  # 读取与写入使用同一错误行为。
    return session  # 返回已经过授权检查的实体。


def list_sessions(
    db: Session, user_id: int
) -> list[SessionResponse]:  # 当前用户的会话摘要。
    return [
        SessionResponse(id=row.id, title=row.title)
        for row in repository.list_sessions(db, user_id)
    ]  # 不暴露其他内部字段。


def list_messages(
    db: Session, session_id: int, user_id: int
) -> list[MessageResponse]:  # 历史消息也要进行身份隔离。
    require_session(db, session_id, user_id)  # 先授权，再查询消息。
    return [
        MessageResponse(role=row.role, content=row.content)
        for row in repository.list_messages(db, session_id)
    ]  # 返回稳定数据契约。


def send_message(
    db: Session, user_id: int, body: ChatInput
) -> ChatResponse:  # 一个问答对应一个数据库事务。
    content = body.message.strip()  # 去掉空白字符。
    if not content:  # DTO 长度校验后仍需业务校验。
        raise BusinessError(422, "消息不能为空")  # 空白内容不会写入数据库。
    if body.session_id is not None:  # 先授权，防止为越权请求发起收费模型调用。
        require_session(db, body.session_id, user_id)  # 当前用户不能使用其他人的会话。
    result = generate_reply(
        content
    )  # 先取得有效回复，再开始新增记录，避免失败留下空会话。
    if body.session_id is None:  # 首次发送时创建会话。
        session = repository.create_session(
            db, user_id, content[:40]
        )  # 标题限制在字段长度内。
    else:  # 已有会话必须先验证归属。
        session = require_session(db, body.session_id, user_id)  # 阻止跨用户写入。
    repository.add_exchange(
        db, session.id, content, result.text
    )  # 只保存已经成功生成的问答。
    db.commit()  # 会话和问答一起提交，异常由会话依赖回滚。
    return ChatResponse(
        session_id=session.id, reply=result.text, mode=result.mode, model=result.model
    )  # 使用明确的响应 DTO，API 层再次验证输出契约。
