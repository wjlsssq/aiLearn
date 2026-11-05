"""业务错误与 HTTP 框架解耦，由应用入口统一映射。"""


class BusinessError(Exception):  # Service 可以抛出，但无需导入 FastAPI。
    def __init__(
        self, status_code: int, message: str
    ):  # 当前接口约定的错误状态与描述。
        super().__init__(message)  # 保留标准异常消息。
        self.status_code = status_code  # 应用层用于响应状态映射。
        self.message = message  # 对外允许显示的业务信息。
