"""认证数据访问，仅负责查询和持久化。"""

from sqlalchemy import select  # 参数化查询。
from sqlalchemy.orm import Session  # 当前事务上下文。
from ..models import AccessToken, User  # 数据实体。


def find_user(db: Session, username: str) -> User | None:  # 按用户名查询。
    return db.scalar(select(User).where(User.username == username))  # 不判断密码。


def get_user(db: Session, user_id: int) -> User | None:  # 按主键读取用户。
    return db.get(User, user_id)  # 身份有效性由 Service 决定。


def get_token(db: Session, digest: str) -> AccessToken | None:  # 按摘要读取登录记录。
    return db.get(AccessToken, digest)  # 不处理 HTTP 状态。


def add_token(
    db: Session, digest: str, user_id: int, expires_at: int
) -> None:  # 将令牌加入当前事务。
    db.add(
        AccessToken(token_hash=digest, user_id=user_id, expires_at=expires_at)
    )  # 提交边界由 Service 控制。
