"""Q01：对同一问题分别使用供应商 SDK 或 LangChain；每次只运行一种方式。"""

import argparse  # 明确选择实验方式，避免一次命令重复调用付费服务。
from openai import OpenAI, OpenAIError  # 直接使用兼容协议 SDK。
from backend.app.core.config import settings  # 与 Web 应用共用同一份本机配置。
from backend.app.core.errors import BusinessError  # 统一显示安全的配置错误。
from backend.app.ai.models.factory import is_model_configured  # 不发请求的配置校验。
from backend.app.ai.models.gateway import (
    SYSTEM_INSTRUCTION,
    generate_reply,
)  # 统一问题边界，便于对比。


def main() -> None:  # 通过模块方式执行：python -m scripts.compare_chat_models。
    parser = argparse.ArgumentParser(
        description="Q01 SDK 与 LangChain 对照实验；每次发起一次真实模型请求"
    )  # 提示实验会真实调用服务。
    parser.add_argument(
        "--implementation", choices=["sdk", "langchain"], required=True
    )  # 必须显式选择一种实现。
    parser.add_argument(
        "--message", default="你能帮助我做哪些事情？"
    )  # 对照时使用相同问题。
    args = parser.parse_args()  # 解析用户的命令参数。
    if (
        settings.chat_mode != "llm" or not is_model_configured()
    ):  # 防止把模拟结果误当模型对比。
        parser.exit(
            1, "请先在 .env 配置模型并设置 CHAT_MODE=llm。\n"
        )  # 不输出任何凭据。
    try:  # CLI 不打印原始网络异常，避免泄露请求头或地址细节。
        if args.implementation == "langchain":  # 复用应用的模型调用边界。
            reply = generate_reply(
                args.message
            ).text  # LangChain 输出已整理的文本结果。
        else:  # 观察供应商 SDK 的原始接口和返回结构。
            with OpenAI(
                api_key=settings.llm_api_key.get_secret_value(),
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout_seconds,
                max_retries=0,
            ) as client:  # 退出时关闭 HTTP 连接池。
                response = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {"role": "user", "content": args.message},
                    ],
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                    extra_body={"thinking": {"type": "disabled"}}
                    if settings.llm_provider == "deepseek"
                    else None,  # 与 LangChain 的 DeepSeek 分支保持相同思考模式。
                )  # SDK 直接构造供应商协议请求。
                reply = (
                    response.choices[0].message.content or ""
                )  # SDK 需要读取供应商的 choices 层级。
        print(
            f"实现：{args.implementation}；配置模型：{settings.llm_model}"
        )  # 只展示实验所需元信息。
        print(reply)  # 两种实现最终都得到文本，但返回对象不同。
    except BusinessError as error:  # 业务错误已去除敏感供应商细节。
        parser.exit(1, f"{error.message}\n")  # 明确非成功退出状态。
    except OpenAIError:  # SDK 直接调用时需要自己负责异常边界。
        parser.exit(
            1, "SDK 调用失败，请检查凭据、模型能力和网络。\n"
        )  # 不把完整异常打印到控制台。


if __name__ == "__main__":  # 导入脚本不会发起收费请求。
    main()  # 用户显式执行时才运行实验。
