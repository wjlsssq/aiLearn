"""只读订单助手：身份、工具白名单与执行预算均由服务端控制。"""

import json
import logging
from pydantic import ValidationError
from langchain_core.messages import ToolMessage
from .order import find_order
from ..ai.models.tool_calling import propose_call, finish_answer
from ..ai.tools.order import TOOL_NAME, create_order_tool
from ..core.config import settings
from ..core.errors import BusinessError
from ..db.session import SessionLocal
from ..schemas.tool_calling import (
    OrderAssistantInput,
    OrderAssistantResponse,
    OrderLookupArgs,
    OrderToolResult,
)


def query_order(user_id: int, body: OrderAssistantInput) -> OrderAssistantResponse:
    if settings.chat_mode != "llm":
        raise BusinessError(503, "智能服务尚未启用，请联系管理员")

    def lookup(order_no: str) -> dict:
        with SessionLocal() as db:  # 只在实际查询时持有连接，等待模型期间不占用事务。
            order = find_order(
                db, user_id, order_no
            )  # 闭包捕获认证身份，模型不能覆盖。
        return OrderToolResult(
            status="found" if order else "not_found",
            message="已读取当前账号订单" if order else "未找到或无权访问该订单",
            order=order,
        ).model_dump()  # 不编造没有接入的物流轨迹。

    tool = create_order_tool(lookup)
    model, messages, decision = propose_call(body.question, tool)
    calls = decision.tool_calls
    if (
        decision.invalid_tool_calls
        or len(calls) > 1
        or (
            calls
            and (
                not isinstance(calls[0].get("id"), str)
                or not calls[0]["id"].strip()
                or len(calls[0]["id"]) > 128
            )
        )
    ):  # 先核对整个提议，再执行；超预算时不允许先执行其中一个。
        return OrderAssistantResponse(
            status="blocked", message="订单查询请求无效，请重新描述查询需求"
        )
    if not calls:
        answer = decision.text.strip() or None
        return OrderAssistantResponse(
            status="complete" if answer else "failed",
            answer=answer,
            message="请提供订单编号以继续查询" if answer else "订单助手未返回有效答复",
        )
    call = calls[0]
    if call["name"] != TOOL_NAME:
        result = OrderToolResult(
            status="unknown_tool", message="工具不在允许名单中，未执行"
        )
    else:
        try:
            arguments = OrderLookupArgs.model_validate(call["args"]).model_dump()
        except ValidationError:
            result = OrderToolResult(
                status="invalid_arguments", message="订单查询参数无效，未执行"
            )
        else:
            try:
                result = OrderToolResult.model_validate(tool.invoke(arguments))
            except Exception as error:
                logging.getLogger(__name__).error(
                    "只读订单工具失败：%s", type(error).__name__
                )  # 日志只记录类型，不暴露 SQL、凭据或供应商私密错误。
                result = OrderToolResult(
                    status="error", message="订单查询暂时失败，请稍后重试"
                )
    tool_message = ToolMessage(
        content=json.dumps(result.model_dump(), ensure_ascii=False),
        tool_call_id=call["id"],  # 原调用 ID 对应原 assistant 消息，不能重造身份。
    )
    try:
        final = finish_answer(model, messages, decision, tool_message)
        if final.tool_calls or final.invalid_tool_calls:
            raise BusinessError(502, "已达到工具执行预算，未继续查询")
        if not final.text.strip():
            raise BusinessError(502, "模型未返回最终正文")
    except BusinessError:
        return OrderAssistantResponse(
            status="failed",
            order=result.order,  # 归纳失败仍保留确定性订单数据，允许用户自行核对。
            message="订单助手暂时无法完成答复，请稍后重试",
        )
    return OrderAssistantResponse(
        status="complete" if result.status in ("found", "not_found") else "failed",
        answer=final.text.strip(),
        order=result.order,
        message=result.message,
    )
