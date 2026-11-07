"""集中注册业务路由，统一 /api 前缀。"""

from fastapi import APIRouter  # 聚合业务路由。
from .routes import auth, chat, health, order, prompt, chain  # 各业务 HTTP 入口。

router = APIRouter(prefix="/api")  # 对外接口保持原路径。
router.include_router(health.router)  # 健康检查。
router.include_router(auth.router)  # 登录认证。
router.include_router(order.router)  # 当前用户订单。
router.include_router(chat.router)  # 聊天与会话。
router.include_router(prompt.router)  # Q02：不调用模型的模板预览。
router.include_router(chain.router)  # Q03：固定流水线实验。
