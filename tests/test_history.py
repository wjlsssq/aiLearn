"""Q04：完整轮次、预算与模板角色验证，不请求模型。"""

import pytest
from backend.app.ai.prompts.history import select_history
from backend.app.ai.prompts.customer_service import build_chat_messages


def test_history_keeps_recent_six_rounds_and_current_question_once():
    rows = [(role, f"{i}-{role}") for i in range(8) for role in ("user", "assistant")]
    history = select_history(rows)
    messages = build_chat_messages("现在的问题{json}", history=history)
    assert len(history) == 12
    assert history[0].content == "2-user"
    assert [m.type for m in messages] == ["system"] + ["human", "ai"] * 6 + ["human"]
    assert messages[-1].content == "现在的问题{json}"


def test_budget_keeps_whole_recent_round_and_does_not_modify_storage():
    rows = [("user", "old"), ("assistant", "old"), ("user", "新"), ("assistant", "答")]
    assert len(select_history(rows, max_chars=2)) == 2
    assert select_history(rows, max_chars=1) == []
    assert len(rows) == 4  # 裁剪不删除数据库记录。


@pytest.mark.parametrize(
    "rows", [[("system", "危险"), ("assistant", "答")], [("user", "半轮")]]
)
def test_invalid_history_cannot_inject_roles(rows):
    with pytest.raises(ValueError):
        select_history(rows)
