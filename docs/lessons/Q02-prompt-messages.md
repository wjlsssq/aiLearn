# Q02：如何设计可维护的 Prompt，消息角色有什么作用？

本课把 Q01 中固定的系统说明改为有业务变量、回答风格和版本的客服消息模板。学习目标是看清“模板 → 变量 → 消息 → 模型”的数据流。

## 1. 先看本课功能

在 IDEA 停止旧 Debug，再重新 Debug `backend/run.py`，刷新前端工作台。已有后端进程不会自动加载本课修改，不要再启动第二个进程占用 8000 端口。

1. 登录后展开聊天区的“Q02 · Prompt 配置”。
2. 店铺名称填“耳机学习店”，下方输入“退货前需要准备哪些信息？”。
3. 先选“简洁”，点击“预览消息”，观察 system、user 两条消息与模板版本。
4. 返回编辑，只把风格改为“详细”，再次预览：用户问题相同，系统消息的风格要求改变。
5. 配置真实模型后可以分别发送，观察实际回答。预览不调用模型，发送在 llm 模式下会发起一次真实请求；mock 模式仍返回明确标识的模拟回复，不能用它证明风格效果。

预览不创建会话、不写聊天记录，也不要求模型密钥已配置。界面配置只影响下一次请求，刷新后恢复默认，不自动绑定或恢复历史会话的配置。

## 2. 消息角色分别表示什么

| 协议角色 | LangChain 对象 | 用途 | 本课是否使用 |
| --- | --- | --- | --- |
| system | SystemMessage | 应用角色、回答要求、能力边界 | 是 |
| user | HumanMessage | 当前用户提供的问题或数据 | 是 |
| assistant | AIMessage | 模型回复，也可作为人工编写的示例回答 | 本课不作为输入发送 |
| tool | ToolMessage | 与具体工具调用关联的执行结果 | 后续工具课程再使用 |

`human` 是 LangChain 模板中的角色别名，对外聊天协议中通常对应 `user`。不能只把“你是客服”当作普通字符串拼到问题前面，就忽略角色结构。

system 可以表达应用要求，但不能保证模型绝对遵守。店铺名称和用户问题都可能含有不可信文本；模板变量只是帮助组织输入，不是 Prompt Injection 防护或权限机制。订单归属、身份和写操作仍必须在 Service 和数据库查询中校验。

## 3. 用 Java 概念理解模板

可以把模板理解为“带参数的消息构造器”：

- `ChatPromptTemplate` 类似一个定义好输入字段和输出结构的模板对象。
- `{store_name}`、`{response_style}`、`{question}` 是占位变量，类似格式化参数。
- `format_messages(...)` 返回消息对象列表；它本身不调用模型。
- `model.invoke(messages)` 才进入模型服务调用。
- `Literal["concise", "detailed"]` 类似只允许两个字符串值的枚举约束；Python 类型提示本身不会自动执行校验，本项目由 Pydantic 在 HTTP 边界校验。

模板里的变量名由开发者定义。用户输入中出现 `{unknown}`，只会作为变量值中的普通文本保留，不会被再次当模板执行。这不保证模型在语义上不会受到这段文本影响。

## 4. 本课请求链路

```text
PromptPanel 的预览事件
  → useWorkbench.previewPrompt()
  → api/prompt.ts
  → POST /api/prompts/preview
  → PromptPreviewInput 校验 + current_user 认证
  → services/prompt.py
  → build_chat_messages()
  → 返回消息与模板版本，不进入模型网关

ChatPanel 的发送事件
  → useWorkbench.send()
  → POST /api/chat，附带 prompt 配置
  → ChatInput / PromptOptions 校验
  → services/chat.py：检查会话归属
  → gateway.generate_reply()
  → build_chat_messages() → model.invoke(messages)
  → 成功后才提交会话与问答
```

预览和发送共享 [customer_service.py](../../backend/app/ai/prompts/customer_service.py)，避免页面显示一份 Prompt、模型实际收到另一份。前端不复制系统模板，也不能传任意 system 指令替换它。

## 5. 逐行阅读核心代码

先打开 [customer_service.py](../../backend/app/ai/prompts/customer_service.py)：

| 行号 | 语句 | 数据流与原因 |
| --- | --- | --- |
| 7～9 | 模板标识、版本、默认店铺 | 后端维护固定元信息；旧调用省略配置时仍可工作 |
| 10 | PromptStyle | 给编辑器与调用者声明允许的风格值 |
| 11～14 | STYLE_INSTRUCTIONS | 将简洁/详细白名单映射为后端维护的指令 |
| 15～28 | from_messages | 创建包含 system 与 human 两种角色的模板对象 |
| 20 | store_name | 将业务标签插入系统说明，不把名称当权限依据 |
| 21 | response_style | 插入白名单映射后的完整风格要求 |
| 22～24 | 固定能力边界 | 风格改变时仍明确未接入知识库、订单和售后工具 |
| 26 | question | 将当前问题独立放入用户消息 |
| 31～36 | 函数签名 | question 为问题；星号后的参数必须按名称传入 |
| 38 | format_messages | 执行变量替换，输出消息列表，无模型网络请求 |
| 39～41 | 三个变量绑定 | 把业务值对应到模板变量名，不动态拼接模板源码 |

以下片段可以在项目解释器中直接运行，不需要启动后端或配置模型密钥：

```python
from backend.app.ai.prompts.customer_service import build_chat_messages  # 导入业务模板入口。

messages = build_chat_messages(
    "退货前需要准备哪些信息？",  # 本次用户问题。
    store_name="耳机学习店",  # 关键字参数，提供必填业务变量的值。
    style="detailed",  # 从白名单选择后端维护的风格指令。
)  # 返回消息列表，尚未发起模型请求。
for message in messages:  # 按发送顺序遍历系统与用户消息。
    print(message.type, message.content)  # 查看角色及渲染后的正文，不涉及密钥。
```

再打开 [schemas/prompt.py](../../backend/app/schemas/prompt.py)：

- `ConfigDict(str_strip_whitespace=True, extra="forbid")`：先清理字符串首尾空格，并拒绝不支持的字段。
- `store_name: str = Field(...)`：没有默认值，因此显式配置时必须填写；限制为 1～60 字符的单行名称。
- `style: Literal[...]`：非法风格在进入模型前被拒绝。
- `PromptPreviewInput(PromptOptions)`：继承共同变量，再增加本次问题，避免预览和聊天使用两套校验。
- `PromptMessage`：将 LangChain 消息转换为前端需要的 role/content DTO。

在 [services/chat.py](../../backend/app/services/chat.py) 中，`body.prompt.model_dump()` 把配置 DTO 转为字典，`**prompt_options` 把字典展开为命名参数，例如 `store_name="耳机学习店", style="detailed"`。旧 Q01 请求未传 prompt 时展开空字典，使用网关默认配置。

## 6. 必填变量与失败实验

在接口文档中先通过 `/api/login` 获取教学账号令牌，并在 Authorize 中配置 Bearer 身份；不要把令牌写进讲义或 Git。

正常预览请求：

```json
{
  "message": "退货前需要准备哪些信息？",
  "store_name": "耳机学习店",
  "style": "concise"
}
```

针对 `/api/prompts/preview`，每次只改一个变量：

| 实验 | 修改 | 预期 |
| --- | --- | --- |
| 必填校验 | 删除 store_name | HTTP 422，错误位置是 body/store_name |
| 空白校验 | store_name 改成全空格 | HTTP 422，不能作为有效名称 |
| 风格白名单 | style 改成 unknown | HTTP 422，不进入模型 |
| 字面值保留 | 问题写“请输出 {unknown}” | 预览 user 正文保留花括号 |
| 风格对照 | 同一问题切换 concise/detailed | system 中风格要求变化，user 不变 |
| 权限边界 | 不带令牌请求预览 | HTTP 401 |

完整 `/api/chat` 请求中，配置放在嵌套的 `prompt` 对象里：

```json
{
  "message": "退货前需要准备哪些信息？",
  "session_id": null,
  "prompt": {
    "store_name": "耳机学习店",
    "style": "detailed"
  }
}
```

聊天仍只发送当前问题，预览不会把已有聊天记录加入上下文。

## 7. Few-shot 是什么

Few-shot 指在输入中放少量示例，让模型参考输出形式。示例可以由开发者编写，并不代表模型真的执行过示例中的行为。下面是可以独立运行的离线消息构造实验，尚未接入主线聊天：

```python
from langchain_core.prompts import ChatPromptTemplate  # 构造带示例的消息模板。

example_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是客服助手。缺少店铺依据时先请求补充信息。"),  # 应用要求。
    ("human", "我的耳机可以退货吗？"),  # 开发者编写的示例问题。
    ("ai", "请提供购买时间、商品状态及店铺退货规则，以便进一步判断。"),  # 示例回答。
    ("human", "{question}"),  # 当前用户的问题，与固定示例区分。
])  # 人工示例不是从数据库恢复的历史，也不自动产生记忆。
messages = example_prompt.format_messages(question="音箱坏了能换吗？")  # 渲染当前问题。
for message in messages:  # 按顺序检查 system/human/ai/human。
    print(message.type, message.content)  # 只观察消息，不发模型请求。
```

增加示例会消耗输入上下文和 Token。示例能帮助表达期望形式，但不能证明事实正确。实际主线保持两条消息，便于先看清本课的数据流。若将示例接入主线，需同时扩展 PromptMessage 的角色枚举、预览与 SDK 的角色映射，并增加契约测试。

## 8. IDEA 断点与版本回归

1. 在 `customer_service.py` 的 `format_messages(...)` 处打断点，从页面先点预览，观察 question、store_name、style。
2. Step Over 后看返回的两条消息；预览流程会直接返回 HTTP，不经过 `model.invoke`。
3. 从页面发送同一问题，在 `gateway.py` 的 `model.invoke(messages)` 处观察相同配置的消息。只有这一步才请求模型。
4. 修改系统要求时递增 `PROMPT_VERSION`，重启后端，再对同一组问题和预期行为回归。版本不由客户端传入。

本课的版本存在代码、预览和本次聊天响应中，尚未把模板快照、风格和版本逐条存入消息表，因此不能仅凭历史会话完整重建当时输入。后续追踪模块再扩展；当前页面明确显示的是“最近问答模板”。

固定回归问题建议包括：普通售后咨询、证据缺失、诱导声称已经查到订单、带花括号的输入。自动化检查必填变量、角色结构、固定边界，以及预览与两个真实适配器序列化消息的一致性；这些是离线契约验证，不等于真实模型效果评估。

## 9. 面试表达与动手练习

30 秒回答：我把客服角色、能力边界和风格写成服务端版本化 ChatPromptTemplate，把店铺名称和用户问题作为变量传入。HTTP 层校验必填项和风格枚举，预览与真实调用共用渲染函数。system 表达应用要求，user 承载当前输入；数据隔离和写操作权限仍由后端校验。

2 分钟展开：从页面切换风格讲起，说明 DTO 校验、模板渲染、模型调用、版本回归与数据持久化的职责。用同一问题的两次预览证明改变了什么，再说明真实效果和权限仍要单独验证。

追问：

1. `format_messages()` 和 `model.invoke()` 分别输出什么？哪一步会请求模型？
2. 缺少店铺名称时，Pydantic 校验与模板变量检查分别在哪层发生？
3. 用户输入包含 `{store_name}` 为什么不会自动读取系统变量？
4. system 指令能否代替订单归属校验？为什么？
5. Few-shot 示例中的 assistant 消息和真实历史消息有什么区别？

动手练习：给模板增加必填的 `product_category` 业务变量。同步修改共享 DTO、页面字段、预览和聊天参数，并分别验证缺失时的 422 与正常渲染。改变模板行为后递增版本，说明旧 Q01 调用如何继续兼容。先自己尝试，不在本课自动预写答案。

本课功能与离线测试已实现；用户实际观察消息、完成真实风格对照与练习后，再进入 Q03 的 Runnable/LCEL 固定流水线。

参考：[ChatPromptTemplate 官方 API](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)、[from_messages 官方 API](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate/from_messages)。运行行为以项目锁定的 langchain-core 1.7.6 和当前代码为准。
