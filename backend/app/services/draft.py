"""Q06：区分结构校验、来源检查和业务授权；本阶段不写数据库。"""

from ..ai.models.draft import extract_draft
from ..core.config import settings
from ..schemas.draft import AfterSalesDraft, DraftInput, DraftReport


def make_draft(body: DraftInput) -> DraftReport:
    if settings.chat_mode == "mock":
        # 固定样例不声称从任意文本成功抽取，页面必须标为模拟。
        draft = AfterSalesDraft(
            order_no=None, issue_type="unknown", reason=None, quantity=None
        )
    else:
        draft = extract_draft(
            body.description
        )  # 模型只产生提议，无数据库或订单工具权限。
    if draft is None:
        return DraftReport(
            mode=settings.chat_mode,
            valid=False,
            issues=["模型输出未通过 JSON / 字段校验，未生成可用草稿"],
        )
    if draft.order_no is not None and draft.order_no not in body.description:
        return DraftReport(
            mode=settings.chat_mode,
            valid=False,
            issues=["订单号未在原文中出现，请明确填写后重新提取"],
        )
    missing = [
        name
        for name in ("order_no", "reason", "quantity")
        if getattr(draft, name) is None
    ]
    if draft.issue_type == "unknown":
        missing.append("issue_type")  # 缺失字段来自服务端判断，不信任模型自报完整性。
    return DraftReport(
        mode=settings.chat_mode, valid=True, draft=draft, missing_fields=missing
    )
