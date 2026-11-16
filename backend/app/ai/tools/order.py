"""Q12：创建订单工具。业务查询由 Service 注入，AI 模块不反向导入业务层。"""

from collections.abc import Callable
from langchain_core.tools import StructuredTool
from ...schemas.tool_calling import OrderLookupArgs, OrderToolDefinition

TOOL_NAME = "lookup_my_order"
TOOL_DESCRIPTION = "按订单号查询当前登录用户的订单状态与教学模拟物流。仅只读查询，不退款、不取消订单。订单号缺失时先向用户询问。"


def order_tool_definition() -> OrderToolDefinition:
    return OrderToolDefinition(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        parameters=OrderLookupArgs.model_json_schema(),
    )


def create_order_tool(lookup: Callable[[str], dict]) -> StructuredTool:
    def lookup_order(order_no: str) -> dict:
        return lookup(order_no)  # 回调闭包捕获认证身份，模型看不到也改不了 user_id。

    return StructuredTool.from_function(
        func=lookup_order,
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        args_schema=OrderLookupArgs,
        infer_schema=False,
    )  # 定义工具不等于执行，必须由后端显式 invoke。
