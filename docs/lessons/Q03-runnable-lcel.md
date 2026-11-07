# Q03：Runnable / LCEL 如何组织调用？

本课面试题：**LCEL / Runnable 如何组织调用，invoke、batch、stream 有什么区别？**

你已经在 Q01 调过模型、在 Q02 看过消息模板。本课把四步组成固定流水线：

```text
dict → 规范化 → dict → Prompt → ChatPromptValue → 模型 → AIMessage → 解析器 → str
```

只处理当前问题，不读取聊天历史、订单或知识库。普通聊天继续沿用已完成的异步流式链路；本课实验面板等待执行结束后展示步骤，不是另一个聊天窗口。

## 1. 先体验功能

1. 在 IDEA 停止旧 Debug，重新 Debug `backend/run.py`，刷新前端 5173 页面。
2. 登录后在 Prompt 配置下面打开“流水线实验”。店铺和风格来自打开时的配置快照。
3. 问题前后保留几个空格，点击“预览步骤”。展开规范化和消息渲染，看空白如何变化。预览只运行前两步，不创建模型、不收费、不保存会话。
4. 选择 `batch`，输入两道互不依赖的问题，再预览。结果按问题 1、问题 2 排列。
5. 点击“运行一题 / 两题”才执行完整链。`CHAT_MODE=llm` 时分别请求真实模型 1 / 2 次，可能产生费用；失败按题显示，模型故障不会伪装成模拟成功。

面板的类型名来自实际对象。例如当前锁定版本的解析结果可能显示 `TextAccessor`，这是 `str` 的子类：`isinstance(result, str)` 成立，但 `type(result) is str` 不一定成立。JSON 接口对外仍是字符串。

## 2. 用 Java 概念理解

| Python / LangChain | Java 类比 | 注意点 |
| --- | --- | --- |
| Runnable | 约定统一执行方法的接口 | 不等于线程，也不代表已经执行 |
| RunnableLambda(fn) | 把普通函数适配为接口实现 | 只创建包装，调用时才运行 fn |
| `a \| b` | `b.apply(a.apply(input))` 的组合 | Python 运算符重载，结果是 RunnableSequence |
| invoke | 普通同步调用 | 阻塞当前调用者，得到完整结果 |
| batch | 多输入的批量调度 | 默认实现通常在线程池中执行，输出顺序对应输入 |
| stream | Iterator 增量迭代 | 不是把完整结果切片假装实时 |
| ainvoke / abatch / astream | 异步方法 / 异步迭代 | 异步和流式是两条不同维度 |

`invoke` 并不只能调模型：模板、普通函数适配器、解析器和整条链都有这个接口。输入输出仍须匹配，统一方法名不会自动修复类型错误。

## 3. 核心代码逐句看

打开 `backend/app/ai/chains/customer_service.py`：

```python
normalize = RunnableLambda(normalize_input).with_config(run_name="normalize")
prompt = CUSTOMER_SERVICE_PROMPT.with_config(run_name="prompt")
prefix = normalize | prompt
chain = prefix | model.with_config(run_name="model") | StrOutputParser().with_config(run_name="parse")
```

- 第一句把普通函数变成 Runnable。`run_name` 给调试回调标记步骤，不会修改问题正文。
- 第二句复用 Q02 模板，没有复制一份系统提示词。模板接收 dict，返回携带消息列表的 `ChatPromptValue`。
- 第三句组合前两步。创建 prefix 本身不处理输入，`prefix.invoke(...)` 才开始执行。
- 第四句继续组合。聊天模型接受 PromptValue，输出 `AIMessage`；`StrOutputParser` 提取文本，不验证业务事实，也不校验 JSON 结构。

`normalize_input` 保留问题内部空格、代码和花括号，只统一 CRLF/CR 换行并移除首尾空白；然后把 `style` 白名单映射成模板需要的 `response_style`。不能把所有空白删掉，否则代码缩进、词间空格和原始含义可能损坏。

`StepTrace` 通过回调记录每一步的实际输出，**没有为展示结果再调用一次模型**。聊天模型结束使用 `on_llm_end`，从 `ChatGeneration.message` 取得消息。追踪只保留在本次请求内，不记录模型配置或供应商原始异常。

## 4. 在 IDEA 打三个断点

请求链：`ChainLab.vue` → `useChainLab.ts` → `api/chain.ts` → `api/routes/chain.py` → `services/chain.py` → LCEL。

1. `normalize_input` 的 `question = ...`：看原始字典和规范化后的问题。观察内部两个空格仍然存在。
2. `run_experiment` 的 `chain.invoke(...)`：单题时 step over，观察输出；也可进入 `StepTrace.on_chain_end` 看 dict 和 ChatPromptValue。两题时在 `chain.batch(...)` 看输入列表与一题一份的 callback 配置。
3. `StepTrace.on_llm_end`：完整运行才进入此处。看 `response.generations[0][0].message` 和文本；随后 `on_chain_end` 的 parse 步骤收到字符串。

`inspect` 走 prefix，model/parse 显示“未执行”是预期结果，不是异常。`run` 如果模型配置缺失，构建前就返回安全错误；某题执行途中失败则报告该题的失败阶段，后续步骤跳过。认证失败发生在链执行前。

## 5. 对照 invoke / batch / stream

在仓库根目录 PowerShell 运行，以下三条都强制离线，不修改 `.env`：

```powershell
& .\.venv\Scripts\python.exe -m scripts.compare_runnables --mock --method invoke
& .\.venv\Scripts\python.exe -m scripts.compare_runnables --mock --method batch
& .\.venv\Scripts\python.exe -m scripts.compare_runnables --mock --method stream
```

`invoke` 返回一个字符串；`batch` 返回两项列表；`stream` 在迭代中得到多段字符串。模拟模型输出很快，终端可能看起来一口气出现，不能仅凭动画判断是否流式。测试直接断言多个 chunk 拼接等于完整正文。

去掉 `--mock` 后跟随 `.env`：若是 llm，每次 invoke/stream 各请求一次，batch 请求两次。本次开发验收未请求付费模型，真实效果由你运行确认。

服务端批量使用：

```python
outputs = chain.batch(inputs, config=configs, return_exceptions=True)
```

`configs` 每题各一份追踪，`max_concurrency=2` 是并发上限。结果按输入顺序，不按完成顺序；异常对象逐项转换成安全提示，不直接返回 `str(error)`。这不是把两道问题塞进一个 Prompt，也不是让第二题继承第一题的回答。

速度还受适配器 batch 实现、服务限流和网络影响；不能承诺两题一定比逐题快一倍。测试用可控慢题/快题验证完成顺序变化仍不串题，并验证一题失败另一题仍有结果。

## 6. 顺序、并行和流式的边界

`normalize | prompt | model | parse` 是顺序依赖：后一步需要前一步结果。`batch` 是对多个独立输入调度这条链；`RunnableParallel` 则是把同一个输入交给多个分支，再汇总为字典，后续需要此功能时再实现。

固定链的路径由代码确定。Agent 会根据模型输出与状态决定后续工具或循环；加一个 `|` 不会自动获得自主决策能力。

`.stream()` 也不保证任何组件都会实时透传。中间插入需要收集完整文本的普通 `RunnableLambda` 可能阻断后续增量；本课规范化位于模型之前，输出解析器支持流式转换，所以 CLI 可迭代模型文本。普通聊天的 SSE、取消、供应商结束标记检查和事务保存仍见 [流式聊天](../08-streaming-chat.md)，实验链不承担聊天保存职责。

## 7. 验收和小练习

- 预览可指出 dict → dict → ChatPromptValue；完整运行可再指出 AIMessage → 字符串。
- batch 两题输出与输入一一对应；能解释批量与多轮对话的区别。
- 阅读 `tests/test_chain.py`，找到规范化失败、模型单题失败和空正文拒绝的检查。测试使用离线模型，不依赖供应商服务。
- 在规范化中增加一条“去掉输入开头的 BOM（`\ufeff`）”规则，先写下为什么不能删除正文中任意位置的同类字符，再用一个具体输入验证。保持内部空格与 JSON 花括号原样。

完成上述练习后进入 Q04：把会话历史真正组织为模型上下文。数据库里有历史记录，本身不等于模型已经有记忆。

## 8. 面试表达

**30 秒：**Runnable 提供统一的 invoke、batch、stream 等调用接口，LCEL 用 `|` 组合它们。我把问题规范化、Prompt、模型和文本解析串成固定链。invoke 得到单题完整结果，batch 调度多个独立输入并保持结果顺序，stream 迭代增量输出。链中各步类型仍要匹配；固定链没有 Agent 的动态工具决策。

**2 分钟补充：**我们通过请求内回调观察实际中间类型，没有重复请求模型。两题各自持有追踪器，限制并发并逐项处理异常，不向页面泄露原始供应商错误。预览只执行前两步，不需要密钥或保存聊天。异步和流式不同，是否能逐块透传取决于链中的组件；普通聊天还要处理取消、完成标记和数据库事务，这些不是 LCEL 自动解决的。

参考：[Runnable 官方接口](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable)、[batch 官方接口](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/batch)。以本项目 `uv.lock` 锁定版本和实际测试为准。
