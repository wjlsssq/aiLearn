"""Q02：已登录用户的 Prompt 预览接口。"""

from fastapi import APIRouter, Depends  # 绑定请求 DTO 与认证依赖。
from ..dependencies import current_user  # 权限仍由后端身份控制。
from ...models import User  # 当前用户的类型。
from ...schemas.prompt import PromptPreviewInput, PromptPreviewResponse  # 预览契约。
from ...services.prompt import preview_prompt  # 路由不自行拼接模板。

router = APIRouter(tags=["Prompt"])  # 在接口文档中独立分组。


@router.post("/prompts/preview", response_model=PromptPreviewResponse)
def preview(body: PromptPreviewInput, user: User = Depends(current_user)):
    """校验输入和身份后返回预览；不要求模型密钥已配置。"""
    return preview_prompt(body)  # 无需把用户身份作为可篡改的模板变量传入。
