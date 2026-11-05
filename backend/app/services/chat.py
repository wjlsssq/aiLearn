"""会话归属、消息校验和问答事务。"""

from sqlalchemy.orm import Session  # 当前业务事务。
from collections.abc import AsyncIterator  # 流式事件按需交付。
from contextlib import aclosing  # 断开时关闭模型生成器。
from dataclasses import dataclass  # 将预检查结果与请求数据库会话分开。
import logging  # 未预期故障只记录类型，不回显供应商私密正文。
from starlette.concurrency import run_in_threadpool  # 同步数据库写入不阻塞异步模型流。
from ..ai.models.gateway import (
    generate_reply,
    stream_reply,
)  # 模型调用细节封装在 AI 集成层。
from ..ai.prompts.customer_service import PROMPT_VERSION  # 与预览使用同一模板版本。
from ..core.config import settings  # 明确报告真实或模拟模式。
from ..db.session import SessionLocal  # 流完成时才打开独立的写入事务。
from ..core.errors import BusinessError  # 与框架解耦的业务错误。
from ..models import ChatSession  # 标注已授权会话类型。
from ..repositories import chat as repository  # SQL 均由 Repository 执行。
from ..schemas.chat import (
    ChatInput,
    ChatResponse,
    SessionResponse,
    MessageResponse,
)  # 聊天请求契约。


def require_session(
    db: Session, session_id: int, user_id: int
) -> ChatSession:  # 统一执行会话所有权检查。
    session = repository.find_session(db, session_id, user_id)  # 数据库筛选 ID 与归属。
    if session is None:  # 不暴露其他用户会话是否存在。
        raise BusinessError(404, "会话不存在")  # 读取与写入使用同一错误行为。
    return session  # 返回已经过授权检查的实体。


def list_sessions(
    db: Session, user_id: int
) -> list[SessionResponse]:  # 当前用户的会话摘要。
    return [
        SessionResponse(id=row.id, title=row.title)
        for row in repository.list_sessions(db, user_id)
    ]  # 不暴露其他内部字段。


def list_messages(
    db: Session, session_id: int, user_id: int
) -> list[MessageResponse]:  # 历史消息也要进行身份隔离。
    require_session(db, session_id, user_id)  # 先授权，再查询消息。
    return [
        MessageResponse(role=row.role, content=row.content)
        for row in repository.list_messages(db, session_id)
    ]  # 返回稳定数据契约。


def send_message(
    db: Session, user_id: int, body: ChatInput
) -> ChatResponse:  # 一个问答对应一个数据库事务。
    content = body.message.strip()  # 去掉空白字符。
    if not content:  # DTO 长度校验后仍需业务校验。
        raise BusinessError(422, "消息不能为空")  # 空白内容不会写入数据库。
    if body.session_id is not None:  # 先授权，防止为越权请求发起收费模型调用。
        require_session(db, body.session_id, user_id)  # 当前用户不能使用其他人的会话。
    prompt_options = body.prompt.model_dump() if body.prompt is not None else {}
    result = generate_reply(
        content, **prompt_options
    )  # 先取得有效回复，再开始新增记录，避免失败留下空会话。
    if body.session_id is None:  # 首次发送时创建会话。
        session = repository.create_session(
            db, user_id, content[:40]
        )  # 标题限制在字段长度内。
    else:  # 已有会话必须先验证归属。
        session = require_session(db, body.session_id, user_id)  # 阻止跨用户写入。
    repository.add_exchange(
        db, session.id, content, result.text
    )  # 只保存已经成功生成的问答。
    db.commit()  # 会话和问答一起提交，异常由会话依赖回滚。
    return ChatResponse(
        session_id=session.id,
        reply=result.text,
        mode=result.mode,
        model=result.model,
        prompt_version=result.prompt_version,
    )  # 使用明确的响应 DTO，API 层再次验证输出契约。


@dataclass(frozen=True)
class PreparedChat:
    user_id: int  # 服务端认证身份，不从用户消息推断。
    body: ChatInput  # 已通过 DTO 校验的本次请求快照。
    content: str  # 去掉首尾空白的问题。


def prepare_stream(db: Session, user_id: int, body: ChatInput) -> PreparedChat:
    """在响应头发出前检查内容与归属，释放只读事务，不创建空会话。"""
    content = body.message.strip()
    if not content:
        raise BusinessError(422, "消息不能为空")
    if body.session_id is not None:
        require_session(db, body.session_id, user_id)  # 越权不能触发模型调用。
    prepared = PreparedChat(user_id=user_id, body=body, content=content)
    db.rollback()  # 释放认证与归属查询的连接，模型生成期间不占数据库事务。
    return prepared


def persist_stream(prepared: PreparedChat, reply: str, metadata: dict) -> ChatResponse:
    """仅在流完整结束后成对保存问答，提交成功后才能发送 done 事件。"""
    with SessionLocal.begin() as db:
        if prepared.body.session_id is None:
            session = repository.create_session(
                db, prepared.user_id, prepared.content[:40]
            )
        else:
            session = require_session(db, prepared.body.session_id, prepared.user_id)
        repository.add_exchange(db, session.id, prepared.content, reply)
        response = ChatResponse(session_id=session.id, reply=reply, **metadata)
    return response  # 事务上下文已经成功提交，避免把仅生成成功当作已保存。


async def stream_message(prepared: PreparedChat) -> AsyncIterator[tuple[str, dict]]:
    """产生 start/delta/done/error；取消和生成失败都不会保存未完成问答。"""
    metadata = {
        "mode": settings.chat_mode,
        "model": settings.llm_model.strip() if settings.chat_mode == "llm" else None,
        "prompt_version": PROMPT_VERSION,
    }
    yield "start", metadata  # 立即确认流已建立，客户端仍需等待 done 才能确认保存。
    parts = []  # 只累计当前回答，成功前不创建会话或消息记录。
    options = prepared.body.prompt.model_dump() if prepared.body.prompt else {}
    try:
        async with aclosing(stream_reply(prepared.content, **options)) as chunks:
            async for text in chunks:
                parts.append(text)
                yield "delta", {"text": text}  # 立即转发模型块，不等待完整回复。
        reply = "".join(parts).strip()
        if not reply:
            raise BusinessError(502, "模型未返回有效文本，请稍后重试")
        response = await run_in_threadpool(persist_stream, prepared, reply, metadata)
        yield "done", response.model_dump()  # 到此才同时确认模型完成与 MySQL 提交。
    except BusinessError as error:
        yield "error", {"status": error.status_code, "message": error.message}
    except (
        Exception
    ) as error:  # CancelledError 属于 BaseException，不会被当成普通失败吞掉。
        logging.getLogger(__name__).error("聊天流处理失败：%s", type(error).__name__)
        yield (
            "error",
            {"status": 500, "message": "回复生成或保存失败，请重新打开会话核对后重试"},
        )
