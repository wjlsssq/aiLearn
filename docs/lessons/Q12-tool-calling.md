# Q12：Function Calling / Tool Calling 的执行过程是什么？

按用户最新安排，跳过文档切分与检索学习线，直接进入 Agent 与业务流程阶段。本课先手动展开一次工具协议，下一课用 `create_agent` 自动组织调用循环；无需先配置 Embedding 或完成 RAG。

场景：用户问“请查询我的订单 DEMO-A001”，模型提出查询请求，后端根据认证用户读取 MySQL，再把工具结果交给模型生成答复。订单、物流都是教学数据；物流只作明确模拟说明，没有接入快递服务。

## 1. 先运行一个工具闭环

在 IDEA 停止旧 Debug，再重新 Debug `backend/run.py`，刷新页面，登录 alice，打开“订单工具实验”。本课不增加依赖、数据库表或环境字段。

- `CHAT_MODE=llm`：点击“查 A001”再运行，最多发起两次真实模型请求，可能产生费用；观察工具参数、调用 ID、MySQL 订单卡片、最终文字。
- `CHAT_MODE=mock`：固定演示查询 DEMO-A001，无论问题写什么都走该固定样例；不理解任意描述、不调用模型。只有订单查询仍是真实教学 MySQL。登录 bob 后固定样例会返回未找到或无权访问。
- 真实模式输入“帮我查订单状态”：模型应先询问订单号，不调用工具；面板显示“数据库未查询”。真实模型行为仍需用户验收。
- 登录 alice 后查询 DEMO-B001：服务端与不存在的订单一样返回“未找到或无权访问”，不得泄露 bob 的商品详情。

实验不写会话、不退款、不取消订单。普通聊天保留 Q04/Q05 能力，暂未自动接入订单工具。实验过程中关闭按钮禁用；登出或页面销毁会拒收旧响应，但不声称撤销已发送的模型请求或费用。

## 2. 核心概念对照

| 对象 | 含义 | Java 类比 |
| --- | --- | --- |
| StructuredTool | 名称、描述、参数 schema 与本机函数 | 服务方法元信息与实现 |
| model.bind_tools | 将工具定义附加到模型请求 | 给决策方接口说明，不是执行 |
| AIMessage.tool_calls | 模型提出的名称、参数和调用 ID | 待校验的方法调用请求 |
| 后端执行器 | 白名单、参数、预算与授权检查 | Service 调度边界 |
| ToolMessage | 执行结果及对应 tool_call_id | 携带关联 ID 的返回值 |
| Agent | 自动组织决策与工具执行循环 | 带状态与停止条件的调度流程 |

模型没有直接连接 MySQL，也不会凭工具名自己运行 Python。模型输出是提议，后端才有权限选择并执行工具。单次 Tool Calling 不等于完整 Agent。

## 3. 真实消息顺序

```text
第一次模型请求：system + human + tools schema
  ↓
assistant: tool_calls=[{id: call-order-1, name: lookup_my_order,
                        args: {order_no: DEMO-A001}}]
  ↓ 后端校验并执行只读查询
tool: tool_call_id=call-order-1, content={status, order, logistics}
  ↓
第二次模型请求：system + human + assistant(tool_calls) + tool(result)
  ↓
assistant: 最终答复
```

工具参数只有 `order_no`。`user_id` 来自 Bearer 认证，在服务端闭包中捕获，不放进模型可填写的 schema。ToolMessage 的 ID 必须对应原 assistant 调用 ID；不能把结果随便拼成一条新 human 消息，也不能漏掉原 assistant 调用。

本课只允许一个工具调用、两次模型请求。不请求工具时只有第一次请求；提出多个调用时整个批次被阻止；第二次又要工具时停止，不再循环。

## 4. 按行读与断点

1. `schemas/tool_calling.py` 的 `OrderLookupArgs`：`extra="forbid"` 和 `strict=True`，拒绝模型夹带 user_id、数字类型订单号及不合约参数。
2. `ai/tools/order.py` 的 `create_order_tool`：查看 StructuredTool 的 name、description、args_schema；函数只接收订单号，业务回调从 Service 注入，AI 模块不反向导入业务服务。
3. `ai/models/tool_calling.py` 的 `model.bind_tools([tool])`：查看定义，再看 decision.tool_calls 与 invalid_tool_calls。绑定后仍需 invoke 才发生网络请求。
4. `services/tool_calling.py` 的协议检查：无效 JSON、无效 ID、多调用超预算都先于查询被阻止。未知工具不动态 import，不 eval，不按名字执行任意函数。
5. `OrderLookupArgs.model_validate`：本地再次严格校验。适配器可能精简供应商 schema；测试发现 wire schema 不一定保留服务端的 additionalProperties，所以模型遵守 schema 不能代替权限控制。
6. `lookup` 回调捕获真实 user_id；执行工具时打开短数据库会话，查询结束就关闭。路由已释放认证读取连接，模型等待期间不持有数据库事务。
7. `repositories/order.py` 的 `find_order`：WHERE 同时包含 user_id 与 order_no，猜到编号仍不能读取他人数据。
8. `ToolMessage(...)`：安全结果转 JSON，通过 tool_call_id 对应模型提议；不返回供应商原始错误或数据库异常正文。
9. `finish_answer`：把第一次 assistant 调用与工具结果一起传回。原模型未绑定工具，这轮用于回答，若仍收到调用就停止，不再次执行。
10. 前端 `useToolCalling.ts` 与 `ToolCallingPanel.vue` 分别管理业务状态和展示。登出后清空并拒收旧响应；卡片来自工具结果，最终文字仍需核对。

## 5. 失败怎样处理？

| 失败 | 本项目行为 |
| --- | --- |
| 调用 delete_order | 未在白名单，零工具执行，回传 unknown_tool |
| 参数夹带 user_id | 本地拒绝，零工具执行，回传 invalid_arguments |
| 查询他人订单 | 执行归属限定查询，得到 not_found，不透露是否存在 |
| 数据库失败 | 安全工具错误，不暴露 SQL 或异常正文 |
| 工具成功、最后模型限流或截断 | 保留订单卡片，最终阶段失败，不再执行工具 |

第一轮供应商失败直接返回安全 HTTP 错误；已有工具轨迹后的失败保存在报告中，不能把“查询成功”误记为“整条流程成功”。本课不自动重试，不展示模型私有思考链，轨迹只有实际动作和结果。

## 6. 面试卡

**30 秒回答**：我用 LangChain 定义只读订单工具，通过 bind_tools 让模型提出名称与参数。服务端校验白名单、参数和预算，从认证上下文注入身份，按用户范围查询 MySQL。结果以对应调用 ID 的 ToolMessage 回填，再调用模型生成答复。工具提议不是授权，schema 也不能代替归属检查。

| 追问 | 结合项目回答 |
| --- | --- |
| 为什么工具描述重要？ | 影响模型何时选择与如何填参；能否执行由后端决定。 |
| 用户 ID 能让模型填吗？ | 不能，身份封在服务端回调闭包，schema 没有该字段。 |
| 工具结果就是最终答案吗？ | 它是结构化观察；模型再组织文字，卡片保留确定性结果。 |
| 多工具请求怎么办？ | 本课整体阻止超预算；Q13 再设计自动循环和工具预算。 |
| 为什么不让模型直接生成 SQL？ | 业务工具给模型最小操作面，SQL 与授权留在后端。 |
| ReAct 与 Tool Calling 的关系？ | Tool Calling 提供动作协议，Agent 可循环决策、行动与观察。 |

练习：增加一个只读订单展示字段，沿 Repository → Service → ToolResult → 前端卡片追踪；不要把身份加进工具参数。用测试构造未知工具、非法参数和第二轮再次调用，解释为何未执行。

运行 `uv run --locked python -m pytest tests -q`，真实 ChatDeepSeek / ChatOpenAI 适配器采用内存 HTTP 协议，配合真实 MySQL；不请求付费模型。真实模型是否选对工具、是否正确澄清仍需用户验收。

官方依据：[LangChain Tool Calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling)、[工具定义](https://docs.langchain.com/oss/python/langchain/tools)、[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)。下一课直接 Q13 `create_agent`，不把文档检索作为前置。
