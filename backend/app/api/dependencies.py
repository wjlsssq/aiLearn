"""HTTP 认证适配与请求依赖。"""

from fastapi import Depends  # 声明依赖生命周期。
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)  # 解析 Bearer 头。
from sqlalchemy.orm import Session  # 数据库类型。
from ..core.errors import BusinessError  # 统一业务错误。
from ..db.session import get_db  # 请求级数据库会话。
from ..models import User  # 已认证用户类型。
from ..services.auth import resolve_user  # 认证规则由 Service 执行。

bearer = HTTPBearer(auto_error=False)  # 缺少凭据统一响应 401。


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:  # HTTP 层只解析并转交凭据。
    if credentials is None:  # 匿名用户不能进入受保护业务。
        raise BusinessError(401, "请先登录")  # 应用统一映射响应。
    return resolve_user(db, credentials.credentials)  # 业务层恢复真实身份。
