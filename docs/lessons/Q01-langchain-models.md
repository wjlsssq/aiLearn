# Q01：LangChain 解决什么问题，为什么不直接调用模型 API？

本课场景：用户在 ShopMind 发送一个问题，后端通过 LangChain 调用 DeepSeek，得到回复后把问答保存到 MySQL。

学习顺序：先跑通一次 → 在 IDEA 观察请求 → 比较 SDK 与 LangChain → 解释选型。只学习单次文本调用，Prompt 模板、多轮上下文、流式响应和 RAG 按后续模块推进。

## 1. 先建立正确认识

DeepSeek 是提供模型推理的服务，SDK 负责与它的 API 通信，LangChain 提供模型、消息等应用组件的统一抽象。LangChain 的适配器内部仍会调用供应商 SDK，它不会在本机凭空产生模型，也不会自动提高回答正确率。

Java 对照：`BaseChatModel` 类似统一接口，`ChatDeepSeek` 是一个实现，`create_chat_model()` 类似根据配置创建实现对象的工厂。业务层通过统一调用边界获取回复，供应商配置集中管理。

| 项目里的对象 | 职责 |
| --- | --- |
| DeepSeek 模型服务 | 实际生成回复 |
| OpenAI 兼容 SDK | 构造 HTTP 请求、认证、解析供应商响应 |
| ChatDeepSeek | 把 LangChain 消息和调用方式适配到 DeepSeek |
| BaseChatModel | 上层可以依赖的统一聊天模型接口 |
| ModelReply | 本项目业务层需要的文本、模式和模型名 |

## 2. 配置并完成第一次真实调用

本机 `.env` 已准备好 DeepSeek 基础配置，密钥保持由用户填写。打开仓库根目录 `.env`，确认以下字段：

```dotenv
# 使用真实模型；需要保留阶段 0 联调时可显式改回 mock。
CHAT_MODE=llm
# DeepSeek 官方服务使用专用 LangChain 适配器。
LLM_PROVIDER=deepseek
# API 基础地址，不要填写到 chat/completions 这一层。
LLM_BASE_URL=https://api.deepseek.com
# 以本次查阅的官方接口模型名作为入门示例。
LLM_MODEL=deepseek-flash
# 仅在本机文件中填写你自己的 API Key。
LLM_API_KEY=
# 网络请求超过该秒数则返回超时错误。
LLM_TIMEOUT_SECONDS=30
# 随机性参数，不是准确率参数。
LLM_TEMPERATURE=0.2
# 限制本课回复长度预算，单位是 token。
LLM_MAX_TOKENS=512
```

DeepSeek 官方当前示例使用 `deepseek-flash`；模型名称会随服务演进，实际以账号可调用列表和[官方首次调用文档](https://api-docs.deepseek.com/quick_start)为准。本课为聚焦基础文本结果，在工厂中明确关闭 DeepSeek 思考模式；其默认行为与开关见[官方思考模式文档](https://api-docs.deepseek.com/guides/thinking_mode/)。

API Key 填好后，**完全停止并重新 Debug `backend/run.py`**，刷新前端。页面右上方聊天标签应变为 `LangChain · deepseek-flash`，发送“你能帮助我做哪些事情？”观察回复。

标签显示的是本地配置；第一次成功收到真实回复，才能确认模型服务、凭据和网络都可用。没有密钥时页面会显示“真实模型待配置”，后端也会拒绝发送。

真实模式失败会明确报错，不自动换成模拟回复。`mock` 只有在 `.env` 显式配置时才生效。

## 3. 沿着代码逐步看

```text
ChatPanel 触发 send 事件
  → useWorkbench.send()
  → api/chat.ts → api/client.ts
  → POST /api/chat
  → api/routes/chat.py
  → services/chat.py
  → ai/models/gateway.py：generate_reply()
  → ai/models/factory.py：create_chat_model()
  → ChatDeepSeek.invoke(messages)
  → DeepSeek HTTP API
  → AIMessage → ModelReply
  → repositories/chat.py → MySQL
  → ChatResponse → 前端显示
```

按这个顺序读以下文件，注释与代码逐行对应：

1. [配置](../../backend/app/core/config.py)：环境字段如何变成 Python 配置对象；`SecretStr` 的 repr 隐藏凭据，真正发请求时才取值。
2. [工厂](../../backend/app/ai/models/factory.py)：配置校验、供应商分支、模型参数与返回的 `BaseChatModel`。
3. [模型边界](../../backend/app/ai/models/gateway.py)：创建消息、调用模型、读取文本、转换错误。
4. [聊天业务](../../backend/app/services/chat.py)：先校验会话归属，模型成功后再新增和提交问答。

本课最关键的三步：

```python
# 创建一个实现统一接口的聊天模型对象，此时还没有发送问题。
model = create_chat_model()
# 将统一消息列表交给模型，底层适配器调用供应商 SDK 和 HTTP API。
result = model.invoke(messages)
# 从统一 AIMessage 中提取文本，不在业务层遍历供应商 choices。
text = result.text.strip()
```

`HumanMessage` 表示当前用户问题，`SystemMessage` 声明当前应用的基本职责。返回的 `AIMessage` 不仅可以包含正文，还可以带用量或响应元数据；本课只使用文本，后续在追踪和评估模块再展开。

## 4. IDEA 断点练习

在 `generate_reply()` 中的 `model = create_chat_model()` 设置断点，Debug `backend/run.py`，从前端发送问题。

1. 观察 `content`：它就是本次用户输入。
2. F8 执行工厂，观察 `type(model)`：选择 DeepSeek 时应为 `ChatDeepSeek`。
3. 观察 `messages`：恰好包含 system 与当前 human 两条消息。
4. F8 执行 `invoke()`，这一行通常会等待网络响应。
5. 观察 `type(result)`、`result.content`、`result.text`。
6. 继续到聊天 Service，观察 `ModelReply` 如何转为数据库记录及 HTTP 响应。

不要在调试求值窗口再次执行 `model.invoke(messages)`：那会额外发送一次真实请求。想观察返回值直接查看变量即可。

即使前端已经显示多条聊天记录，这里仍只有当前问题进入模型。数据库历史和模型上下文是两件事；Q04 再添加多轮记忆。

## 5. SDK 与 LangChain 对照实验

项目已提供 [对照脚本](../../scripts/compare_chat_models.py)。在仓库根目录分别运行，每条命令会发起一次真实请求：

```powershell
# 直接使用 SDK，观察 choices[0].message.content 的返回结构。
uv run --locked python -m scripts.compare_chat_models --implementation sdk --message '你能帮助我做哪些事情？'
# 使用 LangChain，观察统一消息和 AIMessage 接口。
uv run --locked python -m scripts.compare_chat_models --implementation langchain --message '你能帮助我做哪些事情？'
```

两种方式都可以完成当前功能。SDK 路径直接组织供应商协议字段，LangChain 路径通过模型适配器统一消息与调用方式；随着 RAG、工具和工作流增多，统一组件可以减少应用中的重复适配。

本课的两个适配器分支分别是 `ChatDeepSeek` 和 `ChatOpenAI`。兼容协议也可能存在参数、工具、推理内容等差异，不能仅修改 base_url 就假定所有功能兼容。[ChatOpenAI 的接口范围](https://docs.langchain.com/oss/python/integrations/chat/openai)与[ChatDeepSeek 说明](https://docs.langchain.com/oss/python/integrations/chat/deepseek)是后续选型依据。

对照脚本让两条路径使用相同基本说明、问题、温度、输出预算和 DeepSeek 思考开关；回复文本仍可能不同，不把逐字一致作为验收标准。

## 6. 配置与故障实验

| 实验 | 如何操作 | 应观察到的行为 |
| --- | --- | --- |
| 真实回复 | 正确配置 DeepSeek 后发送问题 | 显示真实模式并保存成功问答 |
| 缺少密钥 | 临时清空 Key，重启后端并刷新页面 | 模型待配置；后端拒绝调用 |
| 错误凭据 | 临时填写无效 Key 后重启 | 认证失败，不生成模拟回复 |
| 错误模型名 | 临时改为不存在的名称后重启 | 模型服务错误，不保存空会话 |
| 观察上下文 | 同一会话发送多个问题，断点查看 messages | 当前阶段每次只传当前问题 |
| 显式模拟 | CHAT_MODE 改回 mock 后重启 | 清楚显示模拟模式，不请求模型 |

每次实验只改一个变量，完成后恢复正确配置。HTTP 错误映射、超时和空文本已有离线自动化验证，无需为了练习反复消耗真实调用。

模型调用在新会话写入前完成；模型失败不会留下新建的空会话。已有会话会先进行归属校验，越权请求不会先触发模型调用。数据库事务只能控制本地写入，不能撤销已经发生的供应商推理或费用。

## 7. 面试表达

**30 秒版本：** LangChain 提供面向模型、消息、检索和工具的统一应用组件。我在售后客服中通过模型工厂创建 ChatDeepSeek，用统一消息和 invoke 接口获得 AIMessage，再由业务 Service 保存问答。供应商差异集中在适配器中，业务层更容易扩展。如果只是很小的单供应商脚本，直接使用 SDK 也很合适。

**2 分钟展开：** 先说明业务需求，再解释 SDK 到适配器到业务层的边界，结合代码说明配置、错误映射和持久化行为。最后讲清抽象成本：增加依赖和适配层、需要维护版本兼容，且统一接口不代表所有模型能力一致。

追问练习：

1. `ChatDeepSeek(...)` 和 `invoke(...)` 哪一步才会发送问题？
2. `base_url`、模型名、API Key 分别解决什么问题？
3. 为什么模型接口成功返回，也不能断言店铺允许退货？
4. 温度为 0 是否保证每次输出相同？为什么？
5. 为什么聊天记录已存 MySQL，模型仍不知道上一轮的问题？
6. 更换供应商时，哪些业务代码可以保持不变，哪些能力仍需要重新验证？

## 8. 本课验收与进度

实现包括模型工厂、真实调用边界、页面模式显示、SDK 对照脚本和离线协议验证。**真实 DeepSeek 验收需要用户填写本机密钥后执行，未用测试响应冒充真实模型结果。**

- [ ] 本机配置 DeepSeek Key，重启后完成一次真实问答。
- [ ] 在断点中观察 ChatDeepSeek、两条消息与 AIMessage。
- [ ] 分别运行一次 SDK 与 LangChain 对照。
- [ ] 用自己的话回答本课主问题，并解释一次失败场景。

本课完成后再进入 Q02：可维护的 Prompt 与消息角色，不提前叠加多轮记忆和 RAG。
