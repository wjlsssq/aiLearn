"""把异步业务回调包装成工具，AI 层不反向导入业务或数据库。"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from ...schemas.agent import OrderQueryInput, PrepareAfterSalesInput
from ...schemas.order_export import OrderExportInput


def create_service_tools(
    query: Callable[[str], Awaitable[dict]],
    draft: Callable[[], Awaitable[dict]],
    export=None,
):
    async def query_my_orders(sql: str) -> dict:
        writer = get_stream_writer()
        writer({"event": "activity", "data": {"label": "正在查询订单"}})
        return await query(sql)

    async def prepare_after_sales() -> dict:
        writer = get_stream_writer()
        writer({"event": "activity", "data": {"label": "正在整理售后资料"}})
        return await draft()

    tools = [
        StructuredTool.from_function(
            coroutine=query_my_orders,
            name="query_my_orders",
            args_schema=OrderQueryInput,
            description=(
                f"当前北京时间 {datetime.now(timezone(timedelta(hours=8))):%Y-%m-%d}。"
                "查询当前账号订单，参数 sql 是 MySQL 单条 SELECT。仅有逻辑表 my_orders，"
                "字段 order_no（订单号）、product（商品）、status（状态）；quantity、unit_price、discount_amount、shipping_fee、total_amount（应付）、paid_amount（实付）、refund_amount（已退）；created_at（下单）、paid_at、shipped_at、delivered_at；recipient_name、recipient_phone、province、city、district、address、shipping_company、tracking_no。支持 WHERE、LIKE、IN、"
                "GROUP BY、HAVING、ORDER BY、COUNT/SUM/AVG/MIN/MAX、LIMIT/OFFSET，最多50行、8列；SELECT * 仅返回编号、商品、状态，需要其他字段须显式列出。"
                "不支持其他表、联表、子查询、CTE、注释、写操作或身份字段。身份由后端强制限定。"
                "统计和真实订单信息必须调用本工具，不能猜测；金额单位为人民币元，日期为北京时间，可用 ISO 日期字符串比较；实付 paid_amount 不扣退款，净收款需分别查询实付和 refund_amount 后计算。未知字段为 NULL，不能视作零。"
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

    if export is not None:

        async def export_orders_excel(**arguments):
            get_stream_writer()(
                {"event": "activity", "data": {"label": "正在生成订单 Excel"}}
            )
            return await export(OrderExportInput.model_validate(arguments))

        tools.append(
            StructuredTool.from_function(
                coroutine=export_orders_excel,
                name="export_orders_excel",
                args_schema=OrderExportInput,
                description="按时间范围导出当前账号订单到 Excel。必须提供 start_date/end_date（YYYY-MM-DD，包含首尾天），默认按下单 created_at 筛选；date_field 也可选 paid_at/shipped_at/delivered_at。status 为状态精确匹配，product 为商品包含文本，可省略。不接受 SQL、身份或路径。一次最多 366 天、5000 笔，超限需缩小范围，不导出截断文件；文件有效24小时。日期不清楚先询问用户，不能自行编造；返回的文件卡片即下载入口。",
                handle_validation_error="导出参数无效，请检查日期范围和筛选字段；不要传入 SQL 或身份。",
            )
        )
    return tools
