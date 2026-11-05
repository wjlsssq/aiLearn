"""应用装配入口；业务规则、SQL 和 DTO 放在各自模块。"""

from fastapi import FastAPI, Request  # 应用与异常处理请求类型。
from fastapi.responses import JSONResponse  # 统一 JSON 错误响应。
from .api.router import router  # 聚合后的 API。
from .core.errors import BusinessError  # 框架无关的业务错误。

app = FastAPI(title="ShopMind 学习项目", version="0.1.0")  # /docs 生成接口说明。
app.include_router(router)  # 一处装配全部业务路由。


@app.exception_handler(BusinessError)  # 保持各层错误的一致映射。
async def handle_business_error(
    request: Request, error: BusinessError
) -> JSONResponse:  # 不在 Service 中拼 HTTP 响应。
    return JSONResponse(
        status_code=error.status_code, content={"detail": error.message}
    )  # 保持原有前端错误契约。
