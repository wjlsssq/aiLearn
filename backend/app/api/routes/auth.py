"""登录 HTTP 适配，不包含密码算法或 SQL。"""

from fastapi import APIRouter, Depends  # 路由与依赖声明。
from sqlalchemy.orm import Session  # 请求级数据库会话。
from ...db.session import get_db  # 注入数据库连接。
from ...schemas.auth import LoginInput, LoginResponse  # 请求响应契约。
from ...services.auth import authenticate  # 登录业务入口。
from ..dependencies import current_user, bearer
from fastapi.security import HTTPAuthorizationCredentials
from ...services.auth import sign_out
from ...models import User
from ...schemas.auth import CurrentUserResponse

router = APIRouter(tags=["认证"])  # 按业务域组织 API 文档。


@router.post("/login", response_model=LoginResponse)  # 校验并公开响应结构。
def login(body: LoginInput, db: Session = Depends(get_db)):  # HTTP 入参适配。
    return authenticate(db, body)  # 业务与事务交给 Service。


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(current_user)):
    return CurrentUserResponse(username=user.username)


@router.post("/logout", status_code=204)
def logout(
    user: User = Depends(current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    sign_out(db, credentials.credentials)
