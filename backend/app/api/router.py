"""集中注册业务路由，统一 /api 前缀。"""

from fastapi import APIRouter  # 聚合业务路由。
from .routes import knowledge
from .routes import assistant
from .routes import (
    auth,
    chat,
    health,
    order,
    draft,
)  # 各业务 HTTP 入口。

router = APIRouter(prefix="/api")  # 对外接口保持原路径。
router.include_router(health.router)  # 健康检查。
router.include_router(auth.router)  # 登录认证。
router.include_router(order.router)  # 当前用户订单。
router.include_router(chat.router)  # 聊天与会话。
router.include_router(draft.router)  # Q06：结构化信息提取，无业务写入。
router.include_router(knowledge.router)  # Q07：文档准备，不提前接入问答。
router.include_router(assistant.router)  # 面向业务用户的助手入口。
