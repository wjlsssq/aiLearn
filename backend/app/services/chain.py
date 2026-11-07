"""运行无持久化的教学实验；一题一份追踪，批量失败彼此隔离。"""

import json

from ..ai.chains.customer_service import (
    STAGES,
    StepTrace,
    build_chain,
    build_prefix,
    select_model,
)
from ..ai.models.gateway import safe_model_call
from ..ai.prompts.customer_service import PROMPT_VERSION
from ..core.config import settings
from ..core.errors import BusinessError
from ..schemas.chain import ChainInput, ChainReport, ChainResult, ChainStep
from ..schemas.prompt import PromptMessage


def safe_error(error: Exception) -> str:
    # batch(return_exceptions=True) 返回异常对象，需要逐项转换，不能 str(error)。
    try:
        with safe_model_call():
            raise error
    except BusinessError as known:
        return known.message
    except Exception:
        return "流水线执行失败，请在 IDEA 查看对应步骤"


def make_result(index: int, original: str, trace: StepTrace, error=None):
    values = trace.outputs
    normalized = values.get("normalize", {}).get("question")
    prompt = values.get("prompt")
    messages = (
        [
            PromptMessage(
                role="system" if m.type == "system" else "user", content=m.text
            )
            for m in prompt.to_messages()
        ]
        if prompt is not None
        else []
    )
    reply = values.get("parse")
    if error is None and reply is not None and not reply.strip():
        trace.failed_stage = "parse"
        error = BusinessError(502, "模型未返回有效文本")
    steps = []
    input_types = ("dict", "dict", "ChatPromptValue", "AIMessage")
    for name, input_type in zip(STAGES, input_types):
        value = values.get(name)
        failed = name == trace.failed_stage
        output = None
        if value is not None:
            if name == "normalize":
                output = json.dumps(value, ensure_ascii=False, indent=2)
            elif name == "prompt":
                output = json.dumps(
                    [m.model_dump() for m in messages], ensure_ascii=False, indent=2
                )
            else:
                output = value.text if name == "model" else value
        steps.append(
            ChainStep(
                name=name,
                input_type=input_type,
                status="failed"
                if failed
                else "done"
                if value is not None
                else "skipped",
                output_type=type(value).__name__ if value is not None else None,
                output=output,
            )
        )
    return ChainResult(
        index=index,
        original=original,
        normalized=normalized,
        messages=messages,
        reply=reply if error is None else None,
        error=safe_error(error) if error else None,
        failed_stage=trace.failed_stage,
        steps=steps,
    )


def run_experiment(body: ChainInput, *, inspect: bool = False) -> ChainReport:
    inputs = [{"question": q, **body.prompt.model_dump()} for q in body.questions]
    traces = [StepTrace() for _ in inputs]  # 不能让两题共用可变观察器。
    configs = [{"callbacks": [trace], "max_concurrency": 2} for trace in traces]
    chain = build_prefix() if inspect else build_chain(select_model())
    if body.method == "batch":
        # 默认批量实现在线程池并发，返回顺序仍与输入相同。
        outputs = chain.batch(inputs, config=configs, return_exceptions=True)
    else:
        try:
            outputs = [chain.invoke(inputs[0], config=configs[0])]
        except Exception as error:
            outputs = [error]
    return ChainReport(
        execution="inspect" if inspect else body.method,
        mode=settings.chat_mode,
        model=settings.llm_model
        if settings.chat_mode == "llm" and not inspect
        else None,
        prompt_version=PROMPT_VERSION,
        results=[
            make_result(
                i + 1, q, trace, output if isinstance(output, Exception) else None
            )
            for i, (q, trace, output) in enumerate(zip(body.questions, traces, outputs))
        ],
    )
