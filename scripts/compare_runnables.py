"""Q03：在同一条 LCEL 链上对照 invoke、batch 和 stream。"""

import argparse
from backend.app.ai.chains.customer_service import build_chain, select_model
from backend.app.ai.models.gateway import safe_model_call
from backend.app.ai.prompts.customer_service import DEFAULT_STORE_NAME
from backend.app.core.errors import BusinessError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method", choices=["invoke", "batch", "stream"], default="invoke"
    )
    parser.add_argument("--mock", action="store_true", help="强制离线模拟，不修改 .env")
    args = parser.parse_args()
    questions = ["  退货需要什么资料？\r\n", "商品破损怎么办？"]
    inputs = [
        {"question": q, "store_name": DEFAULT_STORE_NAME, "style": "concise"}
        for q in questions
    ]
    print("模式：离线模拟" if args.mock else "模式：跟随 .env（llm 会产生真实请求）")
    try:
        with safe_model_call():
            chain = build_chain(select_model(mock=args.mock))
            if args.method == "invoke":
                print(chain.invoke(inputs[0]))  # 单个输入，等待最终 str。
            elif args.method == "batch":
                print(
                    chain.batch(inputs, config={"max_concurrency": 2})
                )  # 两题，按输入顺序返回。
            else:
                for text in chain.stream(inputs[0]):  # 实际迭代上游块，不先收集全文。
                    print(text, end="", flush=True)
                print()
    except BusinessError as error:
        raise SystemExit(error.message) from None


if __name__ == "__main__":
    main()
