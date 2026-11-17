"""Q06：一次结构化模型调用，不自动修复、不重试、不保存原始响应。"""

from openai import LengthFinishReasonError, ContentFilterFinishReasonError
from ...core.errors import BusinessError
from ...schemas.draft import AfterSalesDraft
from ..prompts.draft import build_draft_messages
from .factory import create_chat_model
from .gateway import safe_model_call


def extract_draft(description: str) -> AfterSalesDraft | None:
    with safe_model_call():
        model = create_chat_model()  # 复用 DeepSeek 工厂、超时和关闭重试的配置。
        model.disable_streaming = (
            True  # 不继承 Agent 的自动流式回调；此处必须取得完整 JSON 后再校验。
        )
        structured = model.with_structured_output(
            AfterSalesDraft, method="json_mode", include_raw=True
        )  # 显式选兼容的 JSON mode；不是供应商原生 JSON Schema 强约束。
        try:
            result = structured.invoke(
                build_draft_messages(description), stream=False
            )  # 仅一次模型请求。
        except (LengthFinishReasonError, ContentFilterFinishReasonError):
            raise BusinessError(
                502, "草稿未完整生成，请检查输出预算或稍后重试"
            ) from None
            # 当前 SDK 可能在返回 raw 之前就拒绝截断或过滤，不能只检查结果字典。
    raw = result["raw"]  # 仅服务端判断结束原因，不向页面返回模型原始输出。
    if raw.response_metadata.get("finish_reason") != "stop":
        raise BusinessError(502, "草稿未完整生成，请检查输出预算或稍后重试")
    if result["parsing_error"] is not None:
        return None  # 解析器或 Pydantic 拒绝结果，不能变成默认成功草稿。
    parsed = result["parsed"]
    return AfterSalesDraft.model_validate(parsed.model_dump())  # 保持严格字段契约。
