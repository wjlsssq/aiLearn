"""健康检查 HTTP 适配。"""

from fastapi import APIRouter, Depends  # 路由与依赖声明。
from sqlalchemy.orm import Session  # 请求级数据库会话。
from ...db.session import get_db  # 注入数据库连接。
from ...schemas.health import HealthResponse  # 健康响应结构。
from ...services.health import check_health  # 健康业务入口。

router = APIRouter(tags=["健康检查"])  # API 文档分组。


@router.get("/health", response_model=HealthResponse)  # 路径保持兼容。
def health(db: Session = Depends(get_db)):  # 注入会话。
    return check_health(db)  # 不在路由里执行 SQL。
