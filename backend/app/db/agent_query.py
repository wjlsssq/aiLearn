"""智能体专属只读连接；配置缺失时拒绝，绝不回退到 root。"""

from functools import lru_cache

from sqlalchemy import create_engine

from ..core.config import settings
from ..core.errors import BusinessError
from .session import url


@lru_cache(maxsize=2)
def _create_engine(username: str, password: str):
    return create_engine(
        url.set(username=username, password=password),
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=0,
        pool_timeout=5,
        connect_args={"connect_timeout": 5, "read_timeout": 7, "write_timeout": 5},
    )


def get_query_engine():
    username = settings.agent_db_user.strip()
    password = settings.agent_db_password.get_secret_value()
    if (
        not password
        or not username
        or username.lower() == "root"
        or username == settings.db_user
    ):
        raise BusinessError(503, "订单查询服务尚未配置独立只读账号")
    return _create_engine(username, password)
