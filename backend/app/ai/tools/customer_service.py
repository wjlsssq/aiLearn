"""把异步业务回调包装成工具，AI 层不反向导入业务或数据库。"""

from collections.abc import Awaitable, Callable

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from ...schemas.agent import OrderQueryInput, PrepareAfterSalesInput


def create_service_tools(
    query: Callable[[str], Awaitable[dict]], draft: Callable[[], Awaitable[dict]]
):
    async def query_my_orders(sql: str) -> dict:
        writer = get_stream_writer()
        writer({"event": "activity", "data": {"label": "正在查询订单"}})
        return await query(sql)

    async def prepare_after_sales() -> dict:
        writer = get_stream_writer()
        writer({"event": "activity", "data": {"label": "正在整理售后资料"}})
        return await draft()

    return [
        StructuredTool.from_function(
            coroutine=query_my_orders,
            name="query_my_orders",
            args_schema=OrderQueryInput,
            description=(
                "查询当前账号订单，参数 sql 是 MySQL 单条 SELECT。仅有逻辑表 my_orders，"
                "字段 order_no（订单号）、product（商品）、status（状态）。支持 WHERE、LIKE、IN、"
                "GROUP BY、HAVING、ORDER BY、COUNT/MIN/MAX、LIMIT/OFFSET，最多50行。"
                "不支持其他表、联表、子查询、CTE、注释、写操作或身份字段。身份由后端强制限定。"
                "统计和真实订单信息必须调用本工具，不能猜测；字段没有金额、日期或数量。"
                "示例：SELECT status, COUNT(*) AS 订单数 FROM my_orders GROUP BY status"
            ),
            handle_validation_error="查询参数无效，只允许 sql 字符串，请重新生成。",
        ),
        StructuredTool.from_function(
            coroutine=prepare_after_sales,
            name="prepare_after_sales",
            args_schema=PrepareAfterSalesInput,
            description="读取当前授权会话的用户原文并整理售后资料，报告缺失字段。无参数，身份和原文均由后端提供，不改写或补造用户描述。不创建工单、不退款。",
            handle_validation_error="本工具不接受参数，用户原文由后端提供。",
        ),
    ]
