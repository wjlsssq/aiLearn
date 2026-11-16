# Q04：消息入库为什么不等于模型拥有记忆？

本课让 ShopMind 在同一会话中理解连续问题。先说“我喜欢蓝色”，再问“我喜欢什么颜色？”。打开新会话后再次询问，模型不应知道旧会话的颜色。模拟模式仍返回明确的模拟文本，只用于联调，不用于证明模型能记住。

## 1. 面试核心回答

模型本次只能看到请求中的上下文。MySQL 保存消息提供持久化；后端读取授权会话的历史、恢复角色、裁剪并加入本次请求，才让模型获得跨轮信息。它不是修改模型权重，也不是永久记忆。

Java 对照：Repository 读取消息 DTO，Service 检查归属并创建请求快照，Prompt 负责将快照渲染为消息，模型网关发起调用。不要让模型根据用户自报的账号决定查谁的数据。

## 2. 本项目的数据流

```text
session_id + 当前问题
  → Service 校验当前用户的会话归属
  → Repository 从 MySQL 取最近 12 条已提交消息
  → select_history 按完整问答裁剪
  → system + MessagesPlaceholder(history) + 当前 human
  → invoke / astream
  → 完整成功后成对保存本次问答
```

前端不上传历史列表，服务端从 MySQL 重建。刷新页面或后端重启后仍可恢复；新会话传空历史。Q02 模板预览和 Q03 独立实验继续没有历史，只有普通聊天使用当前会话。

## 3. 逐行阅读与断点

1. `app/services/chat.py` 的 `load_history`：新会话返回空列表；已有会话先 `require_session`，再查询，最后裁剪。这是安全边界，模型不能代替它。
2. `app/repositories/chat.py` 的 `recent_messages`：SQL 按 id 倒序并限制条数，避免全量读取；返回时逆转恢复时间顺序。结果是普通字符串元组，生成时不需要 ORM 连接。
3. `app/ai/prompts/history.py` 的 `select_history`：按 user/assistant 配对；从最新轮向前累计正文字符，超过预算整轮舍弃；最后恢复正序，构造 HumanMessage / AIMessage。
4. `app/ai/prompts/customer_service.py` 的 `MessagesPlaceholder`：插入消息列表，保留角色，不把历史拼成一大段 system 字符串。当前问题排在最后，只加入一次。
5. `app/ai/models/gateway.py` 的 `model.invoke(messages)` 或 `model.astream(messages)`：观察实际消息类型、数量和内容，确认颜色信息确实在本次输入中。
6. `prepare_stream`：先取快照再 rollback 释放只读事务。失败、取消不保存半条记录；下一次请求只能读取成功提交的问答。

IDEA 仍运行 `backend/run.py`，由用户停止旧 Debug 再重新启动；本次不会操作现有 8000 服务。

## 4. 裁剪实验

- 连续完成七轮问答，在第八轮断点检查：最多十二条历史消息，加一条 system 和本次 human。
- 阅读 `MAX_HISTORY_CHARS=12000`，测试时用 `select_history(rows, max_chars=2)` 观察整轮保留，预算不足返回空列表。
- 裁剪只影响模型输入，刷新左侧历史仍能看全部成功记录。
- 最近一轮自身超过预算时，历史为空，不跳过这一轮去拼接更老的片段；模型可能需要用户补充上下文。
- 失败或停止的消息只在页面暂存，不会进入下一轮服务端上下文。切换会话后不会继承另一会话历史。

该预算只限制历史正文，不计算 system、当前问题和输出，也不等于供应商 token 上限。生产环境需按供应商 tokenizer 统计总输入并为输出预留空间；本课不声称任意模型都绝不超窗。

## 5. 面试追问

| 追问 | 结合实现回答 |
| --- | --- |
| 为什么不能全量发送历史？ | 延迟、成本随轮次增长，还可能超过上下文窗口；本项目 SQL 限量再整轮裁剪。 |
| 为什么不直接取最后 N 条？ | 可能留下孤立的 assistant；当前问答原子保存，按轮保留完整角色序列。 |
| 会话记忆与 RAG 有何不同？ | 前者来自当前对话，后者检索外部依据；两者都需要显式组织进请求。 |
| 为什么不用全局 Python list？ | 不持久化且容易跨用户串话；本项目 MySQL 按会话归属读取。 |
| 要不要直接套旧版 Memory 类？ | 先明确状态与事务归属；本项目显式装配，未来 Agent 再学习图状态和 checkpointer。 |
| 两个请求同时写同一会话呢？ | 当前各取开始时快照，尚无每会话串行队列，不能承诺并发下严格轮次顺序。 |

官方依据：[MessagesPlaceholder](https://reference.langchain.com/python/langchain-core/prompts/chat/MessagesPlaceholder)、[LangChain 短期记忆](https://docs.langchain.com/oss/python/langchain/short-term-memory)。前者插入消息，后者说明 Agent 会话状态与上下文管理；本课尚未使用 Agent checkpointer。

## 6. 验收清单

- 自动化：`uv run --locked python -m pytest tests -q`，不发起付费模型请求。
- 用户实际调用：同会话记住颜色，刷新后继续，新会话无法获取旧颜色。
- 断点能解释 system / human / ai 的顺序，能说明入库、上下文、裁剪三者差别。
- 能解释字符预算的限制、并发快照限制，以及为什么历史助手文本也不能当作可信业务依据。

Q05 的流式基础已提前实现；完成本课后结合 `docs/08-streaming-chat.md` 学习取消、结束标记和提交边界，再按课程映射推进。
