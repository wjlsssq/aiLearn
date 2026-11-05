"""认证业务与登录事务。"""

import secrets  # 生成不可预测的令牌。
import time  # 校验到期时间。
from sqlalchemy.orm import Session  # Service 持有事务边界。
from ..core.errors import BusinessError  # 与 HTTP 框架解耦的业务异常。
from ..core.security import token_digest, verify_password  # 安全工具。
from ..models import User  # 已验证的用户实体。
from ..repositories import auth as repository  # 数据访问统一委托 Repository。
from ..schemas.auth import LoginInput, LoginResponse  # 登录输入契约。


def authenticate(
    db: Session, body: LoginInput
) -> LoginResponse:  # 校验身份并创建登录凭据。
    user = repository.find_user(db, body.username)  # 查找登录用户。
    if user is None or not verify_password(
        body.password, user.password_hash
    ):  # 不区分用户不存在和密码错误。
        raise BusinessError(401, "账号或密码错误")  # 对外保持一致错误。
    token = secrets.token_urlsafe(32)  # 原始凭据只返回给客户端。
    repository.add_token(
        db, token_digest(token), user.id, int(time.time()) + 86400
    )  # 有效期一天。
    db.commit()  # 登录凭据写入成功后才能返回。
    return LoginResponse(token=token, username=user.username)  # 响应由 API DTO 校验。


def resolve_user(db: Session, token: str) -> User:  # 恢复持久化登录身份。
    record = repository.get_token(db, token_digest(token))  # 查询令牌摘要。
    if record is None or record.expires_at < int(time.time()):  # 验证到期时间。
        raise BusinessError(401, "登录已失效，请重新登录")  # 停止业务操作。
    user = repository.get_user(db, record.user_id)  # 读取实际用户。
    if user is None:  # 已删除用户不能继续登录。
        raise BusinessError(401, "用户不存在")  # 明确拒绝认证。
    return user  # 归属检查基于此身份。
