"""Q12：白名单、严格参数、认证注入与固定执行预算，不运行模型生成的代码。"""

import json
import logging
from pydantic import ValidationError
from langchain_core.messages import ToolMessage
from .order import find_order
from ..ai.models.tool_calling import propose_call, finish_answer
from ..ai.tools.order import TOOL_NAME, create_order_tool, order_tool_definition
from ..core.config import settings
from ..core.errors import BusinessError
from ..db.session import SessionLocal
from ..schemas.tool_calling import (
    ToolExperimentInput,
    ToolExperimentReport,
    ToolStep,
    OrderLookupArgs,
    OrderToolResult,
)


def run_order_tool(user_id: int, body: ToolExperimentInput) -> ToolExperimentReport:
    mode = settings.chat_mode
    report = ToolExperimentReport(mode=mode, status="complete")

    def lookup(order_no: str) -> dict:
        with SessionLocal() as db:  # 每次只读工具单独打开连接，模型等待期间不持有事务。
            order = find_order(db, user_id, order_no)  # 身份只来自路由认证上下文。
        if order is None:
            return OrderToolResult(
                status="not_found", message="未找到或无权访问该订单"
            ).model_dump()
        return OrderToolResult(
            status="found",
            message="已读取当前用户的教学订单",
            order=order,
            logistics="教学模拟：暂无独立物流轨迹，请以订单状态为准",
        ).model_dump()

    tool = create_order_tool(lookup)
    model, messages, decision = propose_call(body.question, tool)
    report.model_calls = 1 if mode == "llm" else 0
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
    ):
        report.status = "blocked"
        report.steps.append(
            ToolStep(
                stage="model",
                label="模型提议",
                status="blocked",
                message="工具调用协议无效或超过一个工具的预算，未执行任何查询",
            )
        )
        return report
    report.steps.append(
        ToolStep(
            stage="model",
            label="模型提议",
            status="done",
            message="提出一个工具调用，尚未查询数据库"
            if calls
            else "未请求工具，数据库未查询",
        )
    )
    if not calls:
        report.answer = decision.text.strip() or None
        if report.answer is None:
            report.status = "failed"
            report.steps[-1].status = "failed"
            report.steps[-1].message = "模型既未给出正文，也未请求工具"
        return report
    call = calls[0]
    arguments = {}
    if call["name"] != TOOL_NAME:
        result = OrderToolResult(
            status="unknown_tool", message="工具不在允许名单中，未执行"
        )
    else:
        try:
            arguments = OrderLookupArgs.model_validate(call["args"]).model_dump()
        except ValidationError:
            result = OrderToolResult(
                status="invalid_arguments",
                message="参数无效，只允许合法的 order_no，未执行",
            )
        else:
            report.tool_executions += 1
            try:
                result = OrderToolResult.model_validate(tool.invoke(arguments))
            except Exception as error:
                logging.getLogger(__name__).error(
                    "只读订单工具失败：%s", type(error).__name__
                )
                result = OrderToolResult(
                    status="error", message="订单查询暂时失败，请稍后重试"
                )
    report.steps.append(
        ToolStep(
            stage="tool",
            label="后端工具执行",
            status="done" if result.status in ("found", "not_found") else "failed",
            message=result.message,
            call_id=call["id"],
            name=call["name"][:80],
            arguments=arguments,
            result=result,
        )
    )
    tool_message = ToolMessage(
        content=json.dumps(result.model_dump(), ensure_ascii=False),
        tool_call_id=call["id"],
    )
    try:
        if mode == "llm":
            report.model_calls += 1
        final = finish_answer(model, messages, decision, tool_message)
        if final.tool_calls or final.invalid_tool_calls:
            raise BusinessError(502, "模型再次请求工具，已达到本课执行预算，未继续查询")
        if not final.text.strip():
            raise BusinessError(502, "模型未返回最终正文")
        report.answer = final.text.strip()
        report.status = (
            "complete" if result.status in ("found", "not_found") else "failed"
        )
        report.steps.append(
            ToolStep(
                stage="model",
                label="工具结果回传与答复",
                status="done",
                message="已构造 ToolMessage，模拟模式返回固定正文，未请求模型"
                if mode == "mock"
                else "已将对应 ToolMessage 回传并取得最终正文",
            )
        )
    except BusinessError as error:
        report.status = "failed"  # 工具成功但最终生成失败时仍保留真实查询卡片。
        report.steps.append(
            ToolStep(
                stage="model",
                label="工具结果回传与答复",
                status="failed",
                message=error.message,
            )
        )
    return report
