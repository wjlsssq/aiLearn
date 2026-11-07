"""Q03：固定 LCEL 流水线，以及仅在本次请求内保留的步骤观察器。"""

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from ..models.factory import create_chat_model
from ..prompts.customer_service import CUSTOMER_SERVICE_PROMPT, STYLE_INSTRUCTIONS
from ...core.config import settings

STAGES = ("normalize", "prompt", "model", "parse")


def normalize_input(value: dict) -> dict:
    """只整理换行和首尾空白；内部空格、代码与花括号仍是原始数据。"""
    question = value["question"].replace("\r\n", "\n").replace("\r", "\n").strip()
    if not question:
        raise ValueError("问题不能为空")
    return {
        "question": question,
        "store_name": value["store_name"],
        "response_style": STYLE_INSTRUCTIONS[value["style"]],
    }


def build_prefix():
    # 普通函数先包装成 Runnable；| 把前一步的输出传给下一步。
    normalize = RunnableLambda(normalize_input).with_config(run_name="normalize")
    prompt = CUSTOMER_SERVICE_PROMPT.with_config(run_name="prompt")
    return normalize | prompt  # dict → dict → ChatPromptValue，不访问模型。


def build_chain(model: BaseChatModel):
    # 模型输出 AIMessage；解析器抽取正文，整条链最终返回 str。
    return (
        build_prefix()
        | model.with_config(run_name="model")
        | StrOutputParser().with_config(run_name="parse")
    )


def select_model(*, mock: bool = False) -> BaseChatModel:
    if mock or settings.chat_mode == "mock":
        # 使用真实 Runnable 模型接口的离线替身；不发送供应商请求。
        return FakeListChatModel(responses=["【模拟回复】这是 Q03 流水线实验。"])
    return create_chat_model()


class StepTrace(BaseCallbackHandler):
    """每题独立观察实际输出，不保存模型配置、密钥、原始异常或全局历史。"""

    run_inline = True

    def __init__(self):
        self.names: dict[UUID, str] = {}
        self.outputs: dict[str, Any] = {}
        self.failed_stage: str | None = None

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        name = kwargs.get("name")
        if name in STAGES:
            self.names[run_id] = name

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        if name := self.names.get(run_id):
            self.outputs[name] = outputs

    def on_chain_error(self, error, *, run_id, **kwargs):
        if name := self.names.get(run_id):
            self.failed_stage = self.failed_stage or name

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self.names[run_id] = "model"

    def on_llm_end(self, response, *, run_id, **kwargs):
        # 聊天模型结束也走 on_llm_end；实际结果位于 ChatGeneration.message。
        self.outputs["model"] = response.generations[0][0].message

    def on_llm_error(self, error, *, run_id, **kwargs):
        self.failed_stage = self.failed_stage or "model"
