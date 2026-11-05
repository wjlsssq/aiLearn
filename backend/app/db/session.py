"""数据库连接、请求级会话和实体基类。"""

from collections.abc import Generator  # 标注依赖生成器的返回类型。
from sqlalchemy import URL, create_engine  # 创建 MySQL 连接池。
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)  # ORM 基类和会话工厂。
from ..core.config import settings  # 数据库层只读取配置，不依赖 HTTP 层。

url = URL.create(
    "mysql+pymysql",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
    query={"charset": "utf8mb4"},
)  # 安全绑定连接参数。
engine = create_engine(
    url, pool_pre_ping=True, pool_recycle=1800, connect_args={"connect_timeout": 5}
)  # 失效连接检测和连接超时。
SessionLocal = sessionmaker(bind=engine)  # 请求之间不共享事务会话。


class Base(DeclarativeBase):  # 所有实体共用元数据。
    pass  # 字段由业务实体定义。


def get_db() -> Generator[Session, None, None]:  # 请求依赖的生命周期由 FastAPI 管理。
    with SessionLocal() as db:  # 退出时关闭连接，并回滚未提交的事务。
        yield db  # 交给当前请求使用。
