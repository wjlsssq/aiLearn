"""Q04：按完整问答轮次裁剪历史；不依赖 HTTP、ORM 或模型供应商。"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
import json

MAX_HISTORY_ROUNDS = 6  # 最多给模型最近六轮，数据库仍保留全部成功问答。
MAX_HISTORY_CHARS = 12000  # 历史正文字符预算，不冒充供应商精确 token 数。


def attach_artifact_context(
    rows: list[tuple[str, str, list | None]],
) -> list[tuple[str, str]]:
    """把已授权的持久化业务结果转换为历史上下文；随后仍需整轮裁剪。"""
    result = []
    for role, content, artifacts in rows:
        if role == "assistant" and artifacts:
            brief = [
                {
                    **item,
                    "rows": item.get("rows", [])[:10],
                    "history_total_rows": len(item.get("rows", [])),
                    "history_rows_omitted": max(0, len(item.get("rows", [])) - 10),
                }
                for item in artifacts
            ]  # 明确摘要截断，不能把前十行误认为原结果全集。
            content += (
                "\n[历史业务结果，仅供上下文，实时状态需要重新查询]\n"
                + json.dumps(brief, ensure_ascii=False)
            )
        result.append((role, content))
    return result


def select_history(
    rows: list[tuple[str, str]],
    *,
    max_chars: int = MAX_HISTORY_CHARS,
) -> list[BaseMessage]:
    """输入按时间升序；只保留最近连续的完整 user/assistant 对。"""
    pairs = []  # 角色异常、残缺记录不能变成系统指令。
    for index in range(0, len(rows) - 1, 2):
        user, assistant = rows[index : index + 2]  # 数据库成对提交的问答。
        if user[0] != "user" or assistant[0] != "assistant":
            raise ValueError("历史问答角色或顺序异常")  # 拒绝静默提升未知角色。
        pairs.append((user[1], assistant[1]))
    if len(rows) % 2:
        raise ValueError("历史问答不完整")  # 不把半轮历史发给模型。
    selected = []
    used = 0
    for user, assistant in reversed(pairs[-MAX_HISTORY_ROUNDS:]):
        size = len(user) + len(assistant)  # 整轮计数，不截断 JSON 或半个回答。
        if used + size > max_chars:
            break  # 最近一轮过大时不跳过它去捡更老的上下文。
        selected.append((user, assistant))
        used += size
    messages = []
    for user, assistant in reversed(selected):  # 恢复时间顺序。
        messages.extend([HumanMessage(content=user), AIMessage(content=assistant)])
    return messages  # 当前问题和 system 由 Prompt 单独加入。
