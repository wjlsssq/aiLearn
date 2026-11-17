"""为一轮聊天绑定认证身份与工具业务；运行时不占用聊天事务。"""

import asyncio
import json
import logging
from contextlib import aclosing
from uuid import uuid4

from langgraph.config import get_stream_writer
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from ..ai.agents.customer_service import stream_agent
from ..ai.prompts.customer_service import build_chat_messages
from ..ai.tools.customer_service import create_service_tools
from ..core.errors import BusinessError
from ..schemas.agent import ChatArtifact
from ..schemas.draft import DraftInput
from .agent_query import execute_order_query
from .draft import make_draft
from .order_export import create_export


async def run_chat_agent(user_id: int, content: str, *, history=None, **options):
    request_id = str(uuid4())
    artifacts = []
    tool_calls = 0
    draft_used = False
    export_used = False

    def reserve_tool():
        nonlocal tool_calls
        tool_calls += 1
        if tool_calls > 3:
            raise BusinessError(502, "已达到本次工具执行预算")

    async def publish(artifact: ChatArtifact):
        value = artifact.model_dump(mode="json")
        if len(json.dumps([*artifacts, value], ensure_ascii=False).encode()) > 65536:
            raise BusinessError(502, "本次结果过多，请缩小查询范围")
        artifacts.append(value)
        get_stream_writer()({"event": "artifact", "data": value})

    async def query(sql: str):
        reserve_tool()  # 回调中再次计数，平行调用也不能绕过执行上限。
        try:
            result = await run_in_threadpool(
                execute_order_query, user_id, request_id, sql
            )
        except (SQLAlchemyError, BusinessError) as error:
            logging.getLogger(__name__).error(
                "查询工具不可用：%s", type(error).__name__
            )
            return {"status": "unavailable", "message": "订单查询暂不可用，请稍后重试"}
        if result.status == "ok":
            await publish(
                ChatArtifact(
                    kind="orders",
                    title="订单查询结果",
                    columns=result.columns,
                    rows=result.rows,
                    truncated=result.truncated,
                )
            )
        return result.model_dump(mode="json")

    async def draft():
        nonlocal draft_used
        reserve_tool()
        if draft_used:
            raise BusinessError(502, "本次资料已整理，请补充信息后再发送")
        draft_used = True  # 嵌套模型每轮最多调用一次，不能用工具循环放大费用。
        source = "\n".join(
            [
                str(message.content)
                for message in history or []
                if message.type == "human"
            ]
            + [content]
        )[-2000:]
        try:
            result = await run_in_threadpool(make_draft, DraftInput(description=source))
        except BusinessError as error:
            logging.getLogger(__name__).warning(
                "资料整理失败：%s", type(error).__name__
            )
            return {"status": "failed", "message": "资料整理暂时失败，请稍后重试"}
        if result.valid and result.draft:
            await publish(
                ChatArtifact(
                    kind="draft",
                    title="售后资料",
                    draft=result.draft,
                    missing_fields=result.missing_fields,
                )
            )
        return result.model_dump(mode="json")

    async def export(filters):
        nonlocal export_used
        reserve_tool()
        if export_used:
            return {
                "status": "rejected",
                "message": "每轮最多生成一个导出文件，请另发一条需求",
            }
        export_used = True
        try:
            artifact = await run_in_threadpool(
                create_export, user_id, request_id, filters
            )
        except BusinessError as error:
            return {"status": "rejected", "message": error.message}
        except SQLAlchemyError as error:
            logging.getLogger(__name__).warning("导出失败：%s", type(error).__name__)
            return {"status": "unavailable", "message": "导出服务暂不可用，请稍后重试"}
        await publish(artifact)
        return {
            "status": "ok",
            "message": "Excel 已生成，问答完成后可在文件卡片下载，有效24小时",
            "row_count": artifact.row_count,
            "filename": artifact.filename,
        }

    messages = build_chat_messages(content, history=history, **options)
    async with aclosing(
        stream_agent(messages, create_service_tools(query, draft, export))
    ) as events:
        async for name, data in events:
            if name == "answer":
                data = {**data, "artifacts": artifacts}
            yield name, data


def collect_chat_agent(user_id: int, content: str, **options):
    async def collect():
        final = None
        async for name, data in run_chat_agent(user_id, content, **options):
            if name == "answer":
                final = data
        return final

    with (
        asyncio.Runner() as runner
    ):  # 同步 HTTP 在工作线程内运行，兼容现有 IDEA 调试入口。
        return runner.run(collect())
