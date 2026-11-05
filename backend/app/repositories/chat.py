"""会话和消息数据访问，禁止脱离用户范围查询会话。"""

from sqlalchemy import select  # 参数化查询。
from sqlalchemy.orm import Session  # 当前事务。
from ..models import ChatMessage, ChatSession  # 会话和消息实体。


def list_sessions(db: Session, user_id: int) -> list[ChatSession]:  # 返回用户会话。
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.id.desc())
        )
    )  # 最近创建的在前。


def find_session(
    db: Session, session_id: int, user_id: int
) -> ChatSession | None:  # 数据范围与 ID 同时约束。
    return db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )  # 不泄露其他用户的会话。


def list_messages(
    db: Session, session_id: int
) -> list[ChatMessage]:  # Service 已先校验会话归属。
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
        )
    )  # 按写入顺序恢复。


def create_session(
    db: Session, user_id: int, title: str
) -> ChatSession:  # 将新会话放进当前事务。
    session = ChatSession(user_id=user_id, title=title)  # 创建实体。
    db.add(session)  # 登记待写入对象。
    db.flush()  # 提前取回主键，当前事务尚未提交。
    return session  # 后续消息引用此 ID。


def add_exchange(
    db: Session, session_id: int, content: str, reply: str
) -> None:  # 成对写入用户消息和回复。
    db.add_all(
        [
            ChatMessage(session_id=session_id, role="user", content=content),
            ChatMessage(session_id=session_id, role="assistant", content=reply),
        ]
    )  # 提交由 Service 统一控制。
