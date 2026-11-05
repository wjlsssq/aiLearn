"""数据库只读健康探针。"""

from sqlalchemy import text  # 固定只读 SQL。
from sqlalchemy.orm import Session  # 数据库会话。


def ping(db: Session) -> None:  # 连接失败时抛出数据库异常。
    db.execute(text("SELECT 1"))  # 不改变业务数据。
