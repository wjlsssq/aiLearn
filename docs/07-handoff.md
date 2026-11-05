# ShopMind 双电脑交接

最后更新：2026-11-05。后续每次完成修改都必须同步维护本文件，并与代码一起提交、推送。最新代码版本以 `git log -1` 为准，不在文档中填写本次提交的自身哈希。

## 1. 每次开工先做

在仓库根目录执行；先确认所在分支是 `main`，并检查是否存在上次未提交的工作。

```powershell
git status --short --branch
git pull --ff-only
Get-Content -Encoding UTF8 AGENTS.md
Get-Content -Encoding UTF8 docs/07-handoff.md
git log -3 --oneline
```

拉取成功后再修改。若工作区改动阻止拉取或分支已分叉，保留现场并核对差异，不能用 reset、强推或丢弃文件来解决。不要在两台电脑同时修改同一批工作：上一台完成提交并成功推送后，下一台再拉取。

当前电脑使用的 GitHub 仓库为 `https://github.com/wjlsssq/aiLearn.git`。本机网络需要时可用 `git -c http.proxy=http://127.0.0.1:7892 pull --ff-only`；这是本机代理地址，另一台电脑仅在确实有该代理时使用，不写入共享配置。

## 2. 用户目标与学习方式

- 用户有 Java / 后端经验，Python 较少，已阅读 Q01 调用链与 SDK 对照讲解，主动要求进入 Q02。
- 通过智能电商售后客服 ShopMind 学习 LangChain，以 20 道面试题对应逐步实现的功能模块。
- 交流、讲义和手写注释用中文。教学核心代码逐行解释用途、数据流与设计原因，用 Java 概念帮助理解。
- 每课先看功能与调用链，再断点、对照实验与面试表达。不要一次推进后续所有模块。
- MySQL 是唯一业务数据库。前后端分层、Prettier 和 E 盘依赖约定见根目录 AGENTS.md。

## 3. 当前实现与边界

### 已完成

- 阶段 0：Vue 3 / TypeScript / Element Plus 工作台，FastAPI、SQLAlchemy、MySQL，登录、订单归属隔离、会话与消息持久化、模拟聊天。
- 前端按页面、组件、composable、API、类型、工具和样式拆分，接入 Prettier；后端按 API → Service → Repository → ORM/DB 分层。
- IDEA 调试入口 `backend/run.py`：单进程、关闭热重载，通过 `asyncio.Runner` 启动服务，绕开 IDEA 2025.1 的旧 pydevd 与 Uvicorn `loop_factory` 参数不兼容问题。
- Q01：模型工厂与网关、DeepSeek 专用 LangChain 适配器、标准兼容适配器、SDK 对照脚本、模型状态展示、安全错误映射和测试。
- Q02：版本化客服 ChatPromptTemplate、店铺名称与简洁/详细风格配置、受认证保护的消息预览；预览与真实聊天使用相同渲染函数，并返回服务端模板版本。
- 按用户明确的交互要求提前实现流式基础：工作台发送即显示用户消息，通过 `/api/chat/stream` 和模型 `astream()` 逐块更新助手文本，可停止、原位重试、输入下一条草稿及切换会话取消。课程学习进度仍停留 Q02，未自动推进后续课程。
- 用户已选择 DeepSeek。示例配置使用 `LLM_PROVIDER=deepseek`、`https://api.deepseek.com`、`deepseek-flash`；具体可用模型需以用户账号及供应商当前文档为准。

### 尚未验收

- 尚未完成本次交接的真实 DeepSeek 调用验收；当前本机已存在密钥配置，但有效性未验证。切换电脑后必须在自己的 `.env` 配置，不在聊天、文档或 Git 中传递密钥。
- Q01 自动化测试使用内存 HTTP 响应验证真实适配器，没有发起付费模型调用；不能将其描述为真实服务验收通过。
- 当前只把系统指令和本次问题发给模型。数据库保存历史不代表模型已经拥有记忆；多轮上下文在 Q04 实现。
- 尚未接入 RAG、订单工具、Agent 和售后操作。前端订单展示并不代表模型可查询订单。

## 4. 另一台电脑恢复环境

源码可以放在方便的位置；下面的项目相对路径均在仓库根目录执行。不要复制现有虚拟环境、node_modules 或 IDE 本机配置。

1. 安装 Git、uv、Node.js（当前验证版本 22.18.0）和 MySQL 8；克隆仓库并阅读 AGENTS.md、本文件。
2. 按 [Python 环境重建](00-environment.md#5-新电脑或重新准备环境) 创建 E 盘运行目录、Python 3.12.13、虚拟环境与目录联接，然后 `uv sync --locked`。不要把已有普通目录覆盖为联接。没有 E 盘时先与用户确认替代盘符，再统一调整脚本和文档。
3. 根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/install_frontend.ps1`，从锁文件将前端依赖安装到 E 盘并创建入口。
4. 仅在没有本机 `.env` 时复制 `.env.example` 为 `.env`，填写本机 MySQL 密码和自己的 `LLM_API_KEY`。原电脑数据库账号由用户提供，另一台应按自己的 MySQL 实际设置填写。
5. 执行 `uv run --locked python -m scripts.init_db`，初始化独立教学库 `langchain_lab` 和合成数据。Git 不同步 MySQL 数据或原电脑会话；另一台会有自己的数据。
6. IDEA 项目解释器选择 `E:\ailearn-runtime\shopmind\venv\Scripts\python.exe`，建议打开仓库根目录；右键 `backend/run.py` → Debug。不要直接运行 routes 或 services 中的文件。
7. 另开终端进入 `frontend`，执行 `npm.cmd run dev -- --port 5173 --strictPort`，浏览器访问 `http://127.0.0.1:5173`。

当前原电脑环境：

| 内容 | 路径 / 版本 |
| --- | --- |
| 源码 | `C:\Users\27959\Desktop\ailearn` |
| Python | 3.12.13，实际在 `E:\ailearn-runtime\shopmind\tools\python` |
| 虚拟环境 | `E:\ailearn-runtime\shopmind\venv` |
| 前端依赖工作目录 | `E:\ailearn-runtime\shopmind\frontend-deps` |
| uv / npm 缓存 | `E:\ailearn-runtime\shopmind\cache` 下对应目录 |
| 项目联接 | `.tools`、`.venv`、`.cache`、`frontend/node_modules` |
| MySQL | 8.0.35，`127.0.0.1:3306`，库 `langchain_lab` |

教学登录账号 `alice` / `bob`，密码均为 `Learn123!`，只用于本地合成数据。后端默认 8000，前端默认 5173。不要启动多个后端争用同一端口；修改 `.env` 或后端代码后停止旧 Debug，再重新启动。

## 5. 代码入口与下一步

当前课程按 [Q02 讲义](lessons/Q02-prompt-messages.md) 继续。后端由用户自己在 IDEA 中 Debug；不要自动启动或重启占用 8000 端口的后台服务。修改后需由用户停止旧 Debug 再重新启动，前端刷新即可。

1. 在页面输入问题和店铺名称，切换简洁/详细风格，先用“预览消息”比较 system 与 user；预览不调用模型。
2. 在 `app/ai/prompts/customer_service.py` 的 `format_messages(...)` 处观察变量和返回消息；页面发送在网关 `model.astream(messages)` 处观察增量，普通 `/api/chat` 或 SDK 对照脚本仍可观察 `invoke()`。链路说明见 [流式聊天](08-streaming-chat.md)。
3. 按讲义完成必填变量、字面花括号、Few-shot 和模板版本练习；真实风格效果由用户实际发送后验收。
4. 模板配置暂只存在当前页面与本次请求，历史聊天不恢复模板快照。Q02 代码完成不代表用户练习已完成；理解后再进入 Q03，不提前添加多轮历史和 RAG。

Q01 的真实服务结果仍未由本次代理确认；如尚未完成，可按 [Q01 讲义](lessons/Q01-langchain-models.md) 补齐：

1. 确认本机 `.env` 完整，重启后端，检查 `/api/health` 显示模型已配置。这个检查不访问供应商，不代表密钥有效。
2. 在 `backend/app/ai/models/gateway.py` 的 `model.invoke(messages)` 处打断点；通过页面发送简单问题，观察 `model`、`messages` 和 `result`，完成一次真实服务验收。
3. 跟踪前端 `useWorkbench.ts` → `api/chat.ts` → 后端 `api/routes/chat.py` → `services/chat.py` → AI 网关 → Repository 入库。
4. 使用 `scripts/compare_chat_models.py` 的 `--implementation sdk` / `langchain` 对照，注意每次命令都会发起一次真实模型请求，具体命令见讲义。
5. 练习“LangChain 与供应商 SDK 的区别”，确认 Q01 理解后再推进 Q02 Prompt 模块。不要提前把历史消息加入本课。

模型调用失败应显示错误，不降级伪装成模拟成功；调用前检查会话归属，失败不留下空会话。模型错误不得返回密钥或供应商原始私密错误正文。

## 6. 验证记录与已知限制

2026-11-05，本次交接提交前重新执行：

- 后端格式：`uv run --locked ruff format --check backend scripts tests`。
- 自动化：`uv run --locked python -m pytest tests -q`，包含真实本机 MySQL 集成与无付费请求的模型契约检查；结果见下方最近交接记录。
- 前端：在 `frontend` 执行 `npm.cmd run format:check` 和 `npm.cmd run build`。
- 已知构建提示：全量引入 Element Plus 使产物大于 Vite 建议阈值，构建可完成，后续再按需优化。
- 本机 MySQL 集成测试只清理测试自己创建的令牌和会话，不清空用户数据。首次运行测试前需初始化种子数据。
- 表结构目前靠 `create_all` 建基线，不会迁移已有列；未来改表要接入 Alembic。
- Codex Windows 受限沙箱中异步 socketpair 曾阻塞；写入 E 盘、运行依赖相关测试可能需要工具权限审核。这是执行环境限制，不要为此改业务代码。

## 7. 每次收工必须做

1. 完成必要检查，在本文件更新当前进度、验证结果、待办及下一步，记录日期；不能将未执行的验证写成通过。
2. 检查 `git diff` 与将要暂存的文件，确认没有 `.env`、真实密钥、IDE 配置、依赖、缓存或构建产物。
3. 将代码和交接文档一起提交，推送 `origin/main`。用户已授权日常提交推送，无需重复询问。
4. 推送被拒绝时先 fetch 并核对远端变动，不强推；保留本地提交，安全整合后重新验证、推送。
5. 向用户报告提交短哈希、是否推送成功和下一台电脑的第一步。不要只做本地提交就宣称同步完成。

### 最近交接记录

- 2026-11-05：整理阶段 0 分层、Prettier、IDEA 调试兼容与 Q01 DeepSeek 接入，建立双电脑交接流程；修正配置路径，确保从仓库根目录读取 `.env`。本机原配置在 `backend/.env`，已在根目录缺失时复制到根目录并保留原文件；以后维护根目录版本，两个文件均不提交。当前密钥有效性及真实服务尚未验收；下一步按第 5 节完成 Q01。
- 本次提交前验证结果：后端 44 个文件格式检查通过，根目录配置定位断言通过，pytest 12 项通过（含真实 MySQL 集成）；前端 Prettier 检查与 TypeScript / Vite 构建通过，仅有已知包体大小提示。真实 DeepSeek 调用未执行。

### 新电脑环境恢复记录

- 2026-11-05：在另一台电脑将源码克隆到 `D:\learn\aiLearn`，通过本机已启用的 `127.0.0.1:7892` 代理完成 `git pull --ff-only`，远端无新增提交。代理仅作为 Git 单次命令参数使用，不修改共享 Git 配置。
- 已将 uv 0.11.1、Python 3.12.13、虚拟环境、前端依赖及缓存安装到 `E:\ailearn-runtime\shopmind`。uv 使用官方发布压缩包并通过发布的 SHA256 校验；本机入口为 `E:\ailearn-runtime\shopmind\tools\uv\uv.exe`，未修改全局 PATH。项目 `.tools`、`.venv`、`.cache`、`frontend/node_modules` 均为指向 E 盘的目录联接，Python 按 `uv.lock`、前端通过 `scripts/install_frontend.ps1` 按 `package-lock.json` 安装。
- 本机 Node.js 为 24.18.0，npm 为 11.16.0，实际 MySQL 服务端为 8.0.45。使用本机 `.env` 成功初始化 `langchain_lab` 和教学账号、订单；本机数据库密码及模型密钥未写入本文件或提交。
- 已在后台启动后端 `http://127.0.0.1:8000` 与前端 `http://127.0.0.1:5173`，服务只监听本机地址。启动日志及进程信息位于项目已忽略的 `runtime` 目录；进程不随 Git 同步，电脑重启后需重新启动。
- 本机验证：环境检查通过；后端 44 个文件格式检查通过，pytest 12 项通过（包含真实本机 MySQL 集成和离线模型适配测试）；前端 Prettier 检查、TypeScript 检查和 Vite 构建通过，仍有已知包体大小提示。实际 HTTP 验证了页面返回 200、后端健康、Vite `/api` 代理、alice 登录、订单 `DEMO-A001` 与会话列表接口。
- 本机健康接口当前显示 `chat_mode=llm`、`model_name=deepseek-flash`、`model_configured=true`。本次没有发送真实模型请求，这些状态不代表密钥和供应商服务已验收；下一步仍按第 5 节完成 Q01 真实调用、断点观察及 SDK 对照。

本机重新启动时，在仓库根目录执行以下命令；前端放在另一个终端运行。若已有服务占用端口，先核对 `runtime` 日志及进程，避免重复启动。

```powershell
# 直接使用项目虚拟环境，避免依赖全局 Python 或 uv 命令。
& '.\.venv\Scripts\python.exe' '.\backend\run.py'

# 另一终端进入前端目录，使用 E 盘依赖启动 Vite。
Set-Location 'D:\learn\aiLearn\frontend'
npm.cmd run dev -- --port 5173 --strictPort
```

### Q02 实现与学习交接

- 2026-11-05：用户阅读 Q01 后要求下一课，已实现 `app/ai/prompts/customer_service.py` 模板模块和 `POST /api/prompts/preview`，前端新增 `PromptPanel`，支持必填店铺名、简洁/详细风格、完整消息预览及模板版本。显式配置缺少店铺名或风格非法时返回 422；旧 Q01 请求省略 prompt 时仍使用后端默认配置。
- 模板标识 `customer-service`、版本 `1.0.0` 由后端维护；模板改动需递增版本并回归固定案例。当前版本不逐条持久化到历史消息，不声称能完整重建过去的 Prompt。SDK 对照脚本也复用默认模板，保持两条调用路径的系统指令一致。
- 验证结果：后端 50 个文件格式检查通过，pytest 26 项通过（真实 MySQL 集成、原有故障与隔离、模板变量和角色检查、两种真实适配器在内存 HTTP 传输中的预览/发送消息一致性）；前端 Prettier、TypeScript、Vite 构建通过，仍有已知大包体提示。
- 浏览器使用独立的 8001/5174 临时服务验证登录、两种风格预览、花括号原样保留、空店铺名字段提示与按钮禁用，以及 375px 小屏布局；未修改用户 IDEA 进程，验收结束后停止临时服务。讲义和学习入口已同步到 README。
- 本次未调用真实模型，不把预览或离线测试标为 DeepSeek 实际风格效果验收。用户需要在 IDEA 重新 Debug 后按 Q02 讲义实际观察和练习；Q01 真实服务验收状态仍保持待确认。
- GitHub 拉取可用，但本机先前没有可用的推送凭据；提交与推送结果以本次收工报告和 `git status` 为准，若身份验证仍失败则保留本地提交，完成登录后再同步，不能强推。

### 即时消息与流式输出交接

- 2026-11-05：用户反馈点击发送后全页禁用、最后整段出现，明确要求即时用户消息和助手流式输出。已提前完成 Q05 的流式基础能力；Q02 学习和练习仍由用户继续，不增加多轮上下文、RAG 或 Agent。
- 前端发送前追加用户消息与等待气泡并清空已发送输入；生成期间可编辑下一条草稿与下一次 Prompt 配置，不再将模型请求绑定到全局 busy。支持停止生成、最后失败/停止问答的原气泡重试、会话切换取消、底部跟随与手动回到最新。
- 后端新增 `/api/chat/stream`，使用真实适配器 `astream()`，由 start/delta/done/error SSE 事件交付。身份与会话归属在请求模型前校验，模型等待期间释放只读事务；完整生成并收到供应商结束标记后，独立事务成对保存问答，再发送 done。故障、空回答、截断流和取消不保存未完成问答；原 `/api/chat` 保留兼容。
- 浏览器使用独立 8001/5174 慢速模拟服务验证了首字前用户消息已出现、部分增量、下一条草稿保留、停止、原位重试不重复气泡、切换新会话不串话。实际数据库检查：成功问答保存一次，停止问答未保存，重试问答成功后保存一次。模拟验收没有请求供应商，没有修改用户 .env 或 IDEA 后端。
- 验证：后端 51 个文件格式检查及 pytest 37 项通过（真实 MySQL、权限、提交失败回滚、取消清理、两种真实适配器的内存 SSE 协议、上游 EOF 缺结束标记与中途连接重置）；前端格式检查、3 项 Node SSE 测试通过，覆盖 UTF-8 中文逐字节分包、CRLF/多行 data/合并帧与截断；TypeScript 和 Vite 构建通过，仅有已知包体提示。
- 限制：取消不能撤销供应商已发生的推理或费用；提交成功但 done 丢失时，需重新打开会话核对再手动重试。本次未新增持久化幂等键，不自动重发模型请求，不声称任意网络故障下严格只执行一次。详细运行与断点说明见 `docs/08-streaming-chat.md`。
- 下一步：用户在 IDEA 停止旧 Debug 并重新运行 `backend/run.py`，刷新 5173 工作台体验真实供应商增量；本次未用真实 DeepSeek 请求验收。临时验收服务和数据清理后退出，保留用户原 8000/5173 服务。
