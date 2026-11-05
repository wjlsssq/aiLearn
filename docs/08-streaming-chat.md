# 聊天交互与流式输出

2026-11-05，用户明确要求改善“点击发送后全页禁用、最后整段出现”的体验，因此提前实现 Q05 的流式基础能力。当前学习课仍是 Q02，不因此自动标记 Q03～Q05 的学习验收完成。

## 页面行为

- 点击发送即追加用户消息与助手等待气泡，立即清空已发送的输入。
- 模型生成期间可以输入下一条草稿、修改下一次 Prompt 配置或查看订单；请求使用发送瞬间的配置快照。
- 模型返回一块正文，页面就追加一块，不通过前端切割完整答案来模拟流式输出。
- 生成期间显示“停止生成”；取消保留已看到的部分和当前输入草稿。切换会话、新建会话、退出登录也会取消当前流，旧事件不能写入新会话。
- 最后一个失败或停止的问答支持在原气泡重试，使用原问题和原配置，不追加重复用户气泡，也不清除后来输入的草稿。开始新问答后，之前未完成气泡不再提供原位重试。
- 用户在底部时跟随增量滚动；向上阅读时保留位置，并提供“回到最新消息”。

失败或停止的气泡是当前页面的临时状态，不是已持久化记录。刷新或重新打开会话会恢复数据库中完整提交的问答。

## 后端链路与事务

保留 `POST /api/chat` 的完整 JSON 响应，供 Q01/Q02 对照与兼容调用；工作台改用 `POST /api/chat/stream`。

```text
发送事件 → useWorkbench：先展示消息、记录问题与配置快照
  → api/chat.ts：POST + Bearer + AbortSignal
  → api/client.ts：fetch + ReadableStream + TextDecoder
  → 后端 routes/chat.py：身份与 DTO 校验
  → services/chat.prepare_stream：空白与归属检查，释放只读事务
  → services/chat.stream_message
  → gateway.stream_reply：相同 Prompt → model.astream(messages)
  → SSE delta → 前端逐块追加正文
  → 模型显式结束 → 独立 MySQL 事务成对写入问答
  → SSE done → 页面确认已保存、刷新会话摘要
```

检查会话归属发生在模型调用前。模型生成期间不持有认证查询或会话查询的数据库事务。完整生成后再打开写入事务，重新检查已有会话归属，原子保存用户问题与助手回复；新会话也在此时才创建。

模型失败、缺少供应商结束标记、空回答或取消，不按成功问答保存。数据库提交失败回滚会话及消息，发 error，不发 done。服务端不会将模型故障降级为模拟成功。

`mock` 是明确标识的教学模拟，按块发送固定回复，不请求供应商，也没有故意增加打字延时；浏览器验收中的慢速流是独立测试服务注入的可控响应，没有改用户 .env。

## 事件协议

响应类型为 `text/event-stream`，每个事件由空行结束，data 是经过 JSON 编码的单行数据。

| event | data | 含义 |
| --- | --- | --- |
| start | mode、model、prompt_version | 流已建立，不代表问答已保存 |
| delta | text | 本次新增加的正文，可包含空格与换行 |
| done | session_id、reply、mode、model、prompt_version | 完整生成且数据库提交成功 |
| error | status、message | 安全错误，客户端保留失败气泡 |

身份、DTO、空白与归属错误发生在响应头前，仍使用普通 HTTP 401/422/404。响应头发出后的模型或数据库故障通过 error 事件表达；不能只看到 HTTP 200 就判定聊天成功。

前端使用 POST fetch 来携带请求体和 Bearer，不使用只支持 GET 构造的原生 EventSource。UTF-8 解码器与 SSE 解析器分别处理中文跨字节分包、一个网络块包含多个事件、CRLF 分隔和截断帧。网络 EOF 不等于 done。

服务端设置 `Cache-Control: no-cache` 和 `X-Accel-Buffering: no`。本机 Vite 代理已验证可逐段传递；未来部署还需检查反向代理与压缩是否缓冲响应。

## 取消、重试与边界

AbortController 断开浏览器流，后端通过异步生成器的清理关闭上游模型读取。尚未完成的回答不提交。取消不保证供应商立即停止已经开展的推理，也不能撤销已发生的费用。

存在“数据库已经提交，但 done 在网络中丢失”的边界。此时前端只能标记保存状态未确认，应先重新打开会话核对，再决定是否手动重试；本次没有新增持久化幂等键，不能声称任何重试都严格只执行一次。没有自动模型重试或自动重发。

多轮上下文仍未接入。流式显示已有历史，不代表模型会收到历史；本次不加入 RAG、工具或 Agent。

## IDEA 调试与验证

修改后由用户停止旧 Debug，再重新 Debug `backend/run.py`，刷新前端；不要额外启动占用 8000 的后台服务。

- 观察模板：`app/ai/prompts/customer_service.py` 的 `format_messages(...)`。
- 观察增量：`app/ai/models/gateway.py` 的 `async for chunk in chunks`。
- 观察事件：`app/services/chat.py` 的 delta 与 done。
- 观察保存：`persist_stream(...)` 的独立事务，done 在提交后产生。
- 观察前端：`useWorkbench.ts` 中 `runTurn()` 的 start/delta/done 分支。

一次请求中仍有多个异步步骤；调试暂停时浏览器等待是正常的。同步 `invoke()` 练习继续通过 `/api/chat` 或 SDK 对照脚本进行，默认工作台使用 `astream()`。

PowerShell 验证命令：

```powershell
# 项目后端格式与所有集成/协议测试，不请求付费模型。
& 'E:\ailearn-runtime\shopmind\tools\uv\uv.exe' run --locked --offline ruff format --check backend scripts tests
& '.\.venv\Scripts\python.exe' -m pytest tests -q

# 前端格式、SSE 分包边界与构建；在 frontend 目录执行。
npm.cmd run format:check
node --test tests/sse.test.mjs
npm.cmd run build
```

参考：[LangChain 模型流式接口](https://docs.langchain.com/oss/python/langchain/models)、[Starlette StreamingResponse](https://starlette.dev/responses/)。运行行为以锁定版本与本项目测试为准。
