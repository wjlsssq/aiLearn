"""登录接口的请求与响应。"""

from pydantic import BaseModel, Field  # DTO 类型和输入校验。


class LoginInput(BaseModel):  # 登录 DTO。
    username: str = Field(min_length=1, max_length=64)  # 限制输入大小。
    password: str = Field(min_length=1, max_length=128)  # 密码只用于当前认证。


class LoginResponse(BaseModel):  # 令牌仅在登录成功时返回。
    token: str  # 当前登录凭据。
    username: str  # 登录用户名称。
