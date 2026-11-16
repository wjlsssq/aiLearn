"""Q04：按完整问答轮次裁剪历史；不依赖 HTTP、ORM 或模型供应商。"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

MAX_HISTORY_ROUNDS = 6  # 最多给模型最近六轮，数据库仍保留全部成功问答。
MAX_HISTORY_CHARS = 12000  # 历史正文字符预算，不冒充供应商精确 token 数。


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
