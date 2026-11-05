"""将数据库连接状态转换为安全的业务错误。"""

from sqlalchemy.exc import SQLAlchemyError  # 只捕获数据库异常。
from sqlalchemy.orm import Session  # 当前会话。
from ..core.config import settings  # 显示当前服务端模式。
from ..ai.models.factory import is_model_configured  # 配置探测不发送收费请求。
from ..core.errors import BusinessError  # 不向前端暴露连接细节。
from ..schemas.health import HealthResponse  # 类型明确的健康状态。
from ..repositories.health import ping  # 只读探针。


def check_health(db: Session) -> HealthResponse:  # 系统健康检查。
    try:  # 数据库不可用时映射明确错误。
        ping(db)  # 不修改业务数据。
    except SQLAlchemyError:  # 不吞掉其他编程错误。
        raise BusinessError(
            503, "MySQL 暂不可用，请检查服务和环境配置"
        ) from None  # 隐藏底层凭据等信息。
    return HealthResponse(
        status="ok",
        database="MySQL",
        chat_mode=settings.chat_mode,
        model_name=settings.llm_model if settings.chat_mode == "llm" else None,
        model_configured=settings.chat_mode == "mock" or is_model_configured(),
    )  # 数据库健康与模型配置状态分别表达。
