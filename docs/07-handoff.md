# ShopMind 双电脑交接

最后更新：2026-11-16。当前目标：可用的企业 Agent 产品；当前实现以本文件前半部分为准，末尾记录为历史，不代表旧实验入口仍存在。每次修改后与代码一同提交、推送，最新版本以 `git log -1` 为准。

## 1. 每次开工先做

在仓库根目录执行，先确认 main 分支和未提交工作：

```powershell
git status --short --branch
git pull --ff-only
Get-Content -Encoding UTF8 AGENTS.md
Get-Content -Encoding UTF8 docs/07-handoff.md
git log -3 --oneline
```

拉取成功后再修改；工作区阻止拉取或分支分叉时保留现场并核对差异，不能 reset、强推或丢弃用户文件。上一台提交并推送成功后，下一台再拉取。

远端为 `https://github.com/wjlsssq/aiLearn.git`。本机当前代理端口是 7897，必要时使用 `git -c http.proxy=http://127.0.0.1:7897 pull --ff-only`；其他电脑先核对自己的代理，不写入共享配置，不套用历史端口。

## 2. 用户方向与长期约定

- 用户有 Java / 后端经验，Python 较少。中文注释与独立讲义保留，通过断点理解实现。
- 2026-11-16 明确要求企业产品页面：只显示真实业务操作与结果，不再放课程编号、技术协议、Prompt、实验面板、演示指标、固定模拟业务输出。后续功能直接按业务流程建设。
- Agent 路线继续 Q12 工具 → Q13 create_agent → Q14 图流程 → Q15 恢复 → Q16 确认与幂等；跳过文档检索学习，不要求配置 Embedding，不把跳过内容记成已学会。
- MySQL 为业务数据库；分层、Prettier、E 盘依赖与敏感文件约定见 AGENTS.md。
- 原有用户改动 `docs/lessons/Q02-prompt-messages.md` 和未跟踪 `docs/面试.md` 保留，不混入功能提交；不要清理、覆盖或自动暂存它们。

## 3. 当前产品实现

- Vue 3 / TypeScript / Element Plus 前端重构为浅灰白底、蓝色强调的服务工作空间。参考 Intercom Inbox、Zendesk Agent Workspace 与 Carbon 模式，具体来源和设计取舍见 [产品设计](09-product-workspace.md)。
- 会话工作台：业务导航、可搜索的当前账号会话、增量回复、停止/重试、下一条草稿、历史恢复、订单上下文。手机有折叠导航、横向会话切换与订单卡片。
- 订单中心：当前账号订单列表和搜索；订单助手抽屉自然语言查询，展示答复和确定性订单卡片。最多一次工具、两次模型调用；尚未接入 create_agent，普通聊天也尚未自动调度订单工具。
- 售后资料：结构化提取订单号、问题类型、原因与数量，提示缺失字段并复制。没有退款、审批或创建工单操作。
- 规则文档：UTF-8 文本保存、同名版本更新、正文与历史版本查阅。已有分块保留为内部入库实现；没有接入 Embedding、检索或自动引用回答，不把资料入库描述成 RAG 已完成。
- 登录不预填或展示开发账号；GET `/api/me` 恢复当前身份。POST `/api/logout` 返回 204，仅撤销当前令牌，不影响其他设备；前端支持无正文响应。
- 订单助手 POST `/api/assistant/orders` 只返回 status、answer、order、message。Service 捕获认证 user_id；工具白名单、严格参数、归属 SQL、短数据库事务和执行预算仍有效。已删除实验报告、步骤计数与模拟物流文案，不为教学结果保留额外服务包装。
- 保留原聊天的事务、取消、历史上下文、SSE 故障保护与供应商适配。客服模板版本 1.2.0，默认店铺名 ShopMind。智能功能要求 llm 配置；mock 仅用于后端回归，页面不提供模拟入口，订单/资料接口在未启用时返回 503。
- Prompt 预览、LCEL 实验、工具协议面板、切分 A/B、流式计时演示及其专属前端状态/类型/接口已删除；后端教学预览、链执行器、对照脚本和示例文档端点退出运行代码。旧讲义对应的实验代码可在 Git 历史 `b3bc15a` 查看。
- 退役接口：`/api/prompts/preview`、`/api/chains/*`、`/api/tool-calling/*`、`/api/knowledge/example`、`/api/knowledge/preview`。当前分层入口见 [架构](05-code-conventions.md)；不要按历史交接恢复实验面板。
- 本次没有新增依赖、环境字段、表结构或迁移；知识表仍为 `0001_knowledge`。现有用户数据及其示例标识原样保留。

## 4. 另一台电脑恢复环境

源码可放在方便的位置，不复制虚拟环境、node_modules 或 IDE 配置。

1. 安装 Git、uv、Node.js 与 MySQL 8，克隆后阅读本文件和 AGENTS.md。
2. 按 [环境恢复](00-environment.md#5-新电脑或重新准备环境) 创建 E 盘运行目录、Python 3.12.13 和目录联接，根目录执行 `uv sync --locked`。没有 E 盘时先确认替代盘符，不覆盖普通目录。
3. 根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/install_frontend.ps1`，从锁文件安装依赖到 E 盘。
4. 仅本机没有 `.env` 时复制 `.env.example`，填写自己的 MySQL 与模型配置；密钥不通过聊天、文档或 Git 传递。
5. 新库先执行 `uv run --locked python -m scripts.init_db`，再执行 `uv run --locked alembic -c backend/alembic.ini upgrade head`。已有库可幂等执行，不清空数据；Git 不同步 MySQL 内容。
6. IDEA 解释器选择 `E:\ailearn-runtime\shopmind\venv\Scripts\python.exe`。打开仓库根目录，右键 `backend/run.py` → Debug。入口通过 asyncio.Runner 绕开旧 IDEA pydevd 的 loop_factory 参数冲突；单进程，无热重载。不要直接运行 routes/services。
7. 另开终端进入 frontend，运行 `npm.cmd run dev -- --port 5173 --strictPort`，访问 `http://127.0.0.1:5173`。

当前电脑源码 `C:\Users\27959\Desktop\ailearn`，Python 3.12.13 / Node 22.18.0 / MySQL 8.0.35。依赖真实目录在 `E:\ailearn-runtime\shopmind`，项目 `.tools`、`.venv`、`.cache`、`frontend/node_modules` 为目录联接。另一台源码曾位于 `D:\learn\aiLearn`，应以其当前工作目录为准。

开发种子账号 alice / bob、密码 Learn123! 仅用于本地合成数据库，不是生产开户方式。生产角色、账号管理和部署尚需建设。

## 5. 本次验证与未完成事项

2026-11-16 企业工作台改造：

- 后端 73 个 Python 文件格式通过，pytest 90 项通过，包含真实 MySQL、令牌撤销、跨用户归属、工具预算/非法参数、两种适配器内存协议、流式/上下文/取消/事务及文档版本回归。模型请求使用替身或内存响应，不消耗真实供应商额度。
- 前端 Prettier、3 项 SSE 测试、vue-tsc 与 Vite 生产构建通过。仅注册实际使用的 Element Plus 组件，中文 locale 已接入。JS 416.49 KB / gzip 147.96 KB，相比全量注册时约 1067 / 349 KB 缩小，无原 JS 大包提示；CSS 380.19 KB / gzip 52.62 KB。
- 浏览器在独立 8001/5174 临时服务验证空白登录、身份恢复、订单查询、规则文档保存/版本、部分流式输出、下一条草稿、刷新后历史恢复及退出；375×812 手机导航和订单卡片无横向溢出，控制台无警告/错误。验收模型为隔离响应，没有调用付费模型。
- 本次唯一命名验收文档/会话已按当前测试用户精确清理，临时服务和浏览器页已关闭；未操作用户 IDEA 和原 8000/5173 服务。预览截图在忽略的 runtime/product-workspace.png 与 runtime/product-mobile-orders.png，不随 Git 同步。
- 未确认真实 DeepSeek 密钥与工具选取效果；配置齐全只说明字段存在，不能声称供应商实际验收通过。生产反向代理、TLS、组织角色、审计、流程恢复与写操作幂等也未完成。
- 取消不能撤销供应商已发生的推理或费用；提交成功但 done 丢失需重新打开会话核对，不承诺严格 exactly-once。

## 6. 下一步

用户停止旧 IDEA Debug 后重新运行 backend/run.py，刷新前端即可看到新页面。按实际账号在本机配置 llm 后自行体验真实回复、订单查询和售后提取；本次不擅自消耗付费额度。

下一阶段围绕实际服务会话接入 create_agent 和授权订单工具，使业务助手按需求选择工具、澄清信息，并保留取消、失败、持久化和权限约束；后续再做显式流程、恢复、人工确认与幂等。技术细节留在注释、调试和研发文档，页面只显示用户需要的执行状态与结果。不将检索配置作为前置，不一次堆入全部未完成功能。

## 7. 每次收工必须做

1. 更新本文件当前状态、验证、未完成事项和下一步，不能将未执行的验证写成通过。
2. 核对 git diff 与暂存内容，不提交 `.env`、密钥、IDE、依赖、缓存、构建产物或用户未授权的原有笔记。
3. 将代码和文档一同提交并推送 origin/main，日常流程已获用户授权，无需重复询问。
4. 推送被拒先 fetch 核对，不强推；保留本地提交并如实说明远端状态。
5. 报告提交短哈希、推送结果，以及另一台电脑先拉取再读交接文档。

---

以下为历史交接记录；旧页面、接口、测试数量和下一步不代表当前状态。

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

### Q03 实现与学习交接

- 2026-11-07：用户要求下一阶段，现进入 Q03 Runnable / LCEL。新增 `app/ai/chains/customer_service.py`，通过 `RunnableLambda | ChatPromptTemplate | model | StrOutputParser` 组成固定链；复用 Q02 模板与已有模型工厂，不改动普通聊天的 SSE、取消和保存行为。
- `/api/chains/inspect` 只执行规范化与 Prompt，不创建模型；`/api/chains/run` 支持单题 invoke、两题 batch。输入上限每题 2000 字、最多两题；两题各一份回调追踪，限制并发 2，结果按输入顺序返回。失败逐题转换为安全提示，不回显供应商原始异常；空白模型正文显示解析失败。实验不创建会话或保存问答。
- 前端增加独立 `useChainLab` 和 `ChainLab`，打开时快照店铺/风格与草稿；显示真实模式的请求次数与费用提示、原始输入、实际步骤类型、展开输出与失败位置。预览和完整执行均与普通聊天状态分离，编辑后清除旧结果，登出后拒收旧响应。
- 当前锁定 LangChain 的 `StrOutputParser` 可能返回 `TextAccessor`（str 子类），面板如实展示；测试用 isinstance 判断字符串契约。模拟模型仍明确标识，未把离线验证描述为真实供应商验收。
- 验证：后端 58 个文件 Ruff 格式通过，43 项 pytest 通过（真实 MySQL、原有流式与归属事务回归、Q03 实际中间类型/多块流/有序批量/独立失败/normalize 与 prompt 定位/空回答/认证与参数校验）；前端 Prettier、3 项 SSE 测试、TypeScript 与 Vite 构建通过，仍有已知 Element Plus 包体提示。CLI invoke / batch / stream 均使用 `--mock` 验证。
- 浏览器在独立 8001/5174 离线服务验证了登录、规范化保留内部空格与 JSON 花括号、单题和双题执行、空白问题禁用、375px 小屏无横向溢出；截图在忽略的 `runtime/Q03-runnable-lab.png`。未改 `.env`，未请求付费模型，未操作用户 8000/5173 进程；临时服务验收后关闭。
- 下一步：用户重新在 IDEA Debug `backend/run.py`，刷新 5173，按 `docs/lessons/Q03-runnable-lcel.md` 先预览，再打断点观察实际对象；按需由用户验收真实 invoke / batch。完成本课 BOM 清理练习、能解释固定链与 Agent 的区别后再进入 Q04 多轮上下文。本次不实现 Q04。


### Q04 实现与学习交接（2026-11-16）

- 用户要求下一阶段。已先拉取 main，远端无新增；本机代理未运行，改用单次禁用代理的 Git 命令成功直连。
- 普通同步与流式聊天先授权，再从 MySQL 有界读取最近六轮问答，按历史正文 12000 字符预算整轮裁剪，通过 MessagesPlaceholder 插入；模板版本升为 1.1.0。生成前释放只读事务，成功仍原子成对写入；新会话不继承历史，失败/取消不进入后续上下文。不更改表结构、不添加依赖。
- 新增讲义 docs/lessons/Q04-conversation-history.md、纯裁剪测试和真实 MySQL 跨请求上下文测试。模型调用使用替身，不发起付费请求；用户需要自行重新 Debug 后验证真实颜色记忆、刷新恢复和新会话隔离。
- 当前是字符预算，不是精确 token 预算，不保证任意模型绝不超窗；并发同会话请求各取开始时快照，尚未串行化。没有新增摘要、长期记忆或 Agent checkpointer。
- 验证：pytest 48 项通过（含真实 MySQL 与旧流式回归），前端 Prettier / TypeScript / Vite 构建通过，仍有原有包体提示；最终模板版本更新后再次回归 48 项通过，60 个 Python 文件格式检查通过，3 项 Node SSE 测试通过。
- 开工时已有用户改动 docs/lessons/Q02-prompt-messages.md 和未跟踪 docs/面试.md，原样保留，不混入本次功能提交。不要清理或覆盖。
- 下一步：按 Q04 讲义打断点观察 history 和 messages，确认理解持久化与上下文区别；Q05 流式基础已提前实现，可在本课后专题学习结束标记、取消与事务边界。未操作用户 IDEA 或 8000 服务。


### Q05 实现与学习交接（2026-11-16）

- 用户要求 Q04 后下一阶段，进入 Q05 流式专题；基础能力已提前实现，本次补上每次请求的首段正文耗时、完成/结束耗时、文本块数与保存状态，以及独立课程讲义。
- 新增 frontend/src/utils/stream-metrics.ts，使用 performance.now 单调时钟。只计非空正文块，不把 start 当首字；done 后不累计会话列表刷新，失败/停止也结束测量；重试重置，历史恢复不伪造旧指标。数据仅留当前页面，无新增依赖或数据库字段。
- 修正网关结束判定：纯文本流只认可 finish_reason=stop，length 输出截断及 content_filter 不保存成完整成功问答；保留部分显示，继续使用 error 事件。两种真实适配器均有内存协议测试，没有付费请求。
- 本次保留 Q04 历史、旧 SSE 协议、认证与归属、取消及事务边界；没有操作用户 IDEA 后台服务。用户重新 Debug 后可按 Q05 讲义观察真实首段/完成耗时、停止并核对数据库。断点等待会影响测量。
- 验证：52 项 pytest 通过（含真实 MySQL 与原有上下文/流式回归）、5 项前端计时/SSE 测试通过、Prettier 与 TypeScript/Vite 构建通过；真实供应商取消和费用行为未实测，不承诺停止即撤销费用或网络断线下 exactly-once。
- 本机原有 Q02 讲义改动和 docs/面试.md 继续保留，不混入功能提交。
- 下一步：先读 docs/lessons/Q05-streaming-cancellation.md 并完成首段/完成/取消实验；理解后进入 Q06 结构化输出。当前仍有原 Element Plus 包体提示。


### Q06 实现与学习交接（2026-11-16）

- 用户看完 Q05 要求下一阶段，新增独立“售后草稿”面板和受认证保护 POST /api/drafts/extract。用户描述只用于本次提取，不读历史、不查订单、不写表、不创建工单。
- Pydantic 严格 schema 定义 order_no / issue_type / reason / quantity；字段必填但允许明确 null，拒绝额外字段、隐式类型、非法枚举和数量范围错误。JSON mode 显式传 schema 指令，include_raw 解析失败不给可用草稿；SDK 可能提前抛出的 length/filter 异常单独安全处理。不返回原始响应、不自动修复或重试。
- Service 另检查订单号在原文中出现并计算缺失字段；不声称该检查证明订单归属、语义事实或售后资格。面板只读展示待核对结果，编辑原描述重新提取。模拟模式返回明确固定空样例；Schema 版本 1.0.0。
- 沿现有架构新增 draft 的 API / Schema / Service / AI 消息与调用模块，前端新增组件 / composable / API / 类型；不添加依赖与数据库字段。核心注释和讲义见 docs/lessons/Q06-structured-output.md。
- 先执行 git pull：直连被重置，发现当前系统代理是 127.0.0.1:7897 后单次指定代理成功，无远端更新；没有修改共享 Git 配置。后续网络问题先检查系统实际代理，不套旧 7892。
- 验证：69 项 pytest 通过（含真实 MySQL、原流式/上下文与 Q06 两种适配器内存 HTTP）、5 项前端计时/SSE 测试通过，Prettier / TypeScript / Vite 构建通过，仍有原 Element Plus 包体提示。真实 DeepSeek 提取效果仍待用户配置并体验，本次协议测试不调用付费服务，未操作用户 IDEA 或 8000 进程。
- 原有 Q02 讲义改动和 docs/面试.md 保留且不混入提交。下一步由用户重新 Debug 后打开售后草稿，按 Q06 讲义实验完整描述、缺订单号、unknown 类型与字段校验，再进入 Q07 RAG。


### Q07 实现与学习交接（2026-11-16）

- 用户要求 Q06 后下一课，进入 RAG 文档准备：上传/粘贴 UTF-8 .txt / .md、A/B 切分对比、来源行与码点范围、原文高亮、MySQL 原文/版本/分块持久化。尚无 Embedding、检索或引用回答；普通聊天不读取已导入规则。
- 新依赖 langchain-text-splitters==1.1.3 已通过 uv 安装到 E 盘，pyproject.toml 与 uv.lock 同步。每次拉取后先 uv sync --locked；本次没有新增前端依赖。
- 第一次启用 Alembic，backend/alembic.ini + backend/migrations 管理新增知识表，revision=0001_knowledge。本机已 upgrade 到 head。旧五张业务表仍由 init_db 创建，脚本已限定基线表，不会偷偷 create_all 新知识表。另一台电脑必须先 init_db（新库），再执行 uv run --locked alembic -c backend/alembic.ini upgrade head；不能 stamp 冒充执行，也不要 downgrade 删除知识数据。Windows INI 保持 ASCII，中文说明在 env.py 与迁移中，避免本地 GBK 解码失败。
- 唯一文档键由当前用户与规范化标题确定；同文档当前 fingerprint 相同复用，内容/参数/算法改变追加版本并原子切换 active_revision，历史仍可追溯。A→B→A 会新增版本，不自动恢复旧版号。MySQL upsert+行锁串行同文档导入，先释放认证旧快照，防止并发等待后读到旧版本。未来检索必须按用户和当前有效版本过滤。
- 切分按 Python 字符数，最多 20000 个原文码点、512 块；块大小 64～2000，重叠 0～1000 且小于块大小。BOM / CRLF 规范化后定位，保留其他空白，逐块检查 source[start:end]；前端 Array.from 做码点高亮。标题只取块起点前最近的 Markdown 标题，非完整文档语法解析，不支持 PDF/Word/表格专用解析。
- 验证：78 项 pytest 通过（真实 MySQL、来源覆盖、重复正文、emoji、版本与参数变化、跨用户隔离、写入故障回滚、并发重复导入）；5 项前端测试通过。TypeScript 初次发现输入数字回调类型缺失，修正后 Prettier / TypeScript / Vite 构建通过，仅有原 Element Plus 大包体提示。最终收工再次确认 76 个 Python 文件格式通过，init_db 与 Alembic upgrade 重复执行通过，仍为 0001_knowledge head；78 项后端与 5 项前端测试及构建均通过。
- 使用 computer-use 浏览器能力在独立 8001/5174 服务验证双参数对比、重复导入复用、参数变更生成 v2、历史 v1 仍可查看、原文高亮；375px 宽度下页面 scrollWidth=375，没有横向溢出。截图 runtime/Q07-knowledge-preview.png 已忽略、不随 Git 同步。唯一命名验收文档已精确清理，临时服务已停止，未操作用户 IDEA 8000/5173，未调用付费模型。
- 当前是用户私有教学规则库，未实现共享店铺管理员角色；未来共享规则发布必须另做授权。原有 Q02 讲义和 docs/面试.md 的用户改动继续保留，不混入本次提交。
- 下一步：用户重新 Debug 后打开“规则知识库”，按 docs/lessons/Q07-document-chunking.md 对比边界、重叠与版本。理解后进入 Q08 Embedding、相似度与 Top-K；届时确认可用的 Embedding 服务，不默认聊天服务支持 Embedding。


### 路线调整与 Q12 Agent 阶段交接（2026-11-16）

- 用户明确要求跳过文档切分检索，直接进入 Agent 与业务流程阶段。已写入 AGENTS.md、README 和课程计划：当前 Q12 Tool Calling → Q13 create_agent → Q14 LangGraph → Q15 恢复 → Q16 用户确认与幂等；不要求先学 Q08～Q11 或配置 Embedding，不把跳过内容标成已学会。Q07 已有代码与可选入口保留。
- 新增受认证保护的 /api/tool-calling/schema 与 /run，以及独立“订单工具实验”面板。一次决策、至多一个只读工具、一次结果回传，最多两次模型请求；普通流式聊天暂不自动调用工具，不保存实验问答，不退款或建单。
- lookup_my_order 工具只有严格 order_no 参数，身份来自路由 Bearer 认证，在 Service 回调中捕获 user_id。模型、前端或工具参数都不能覆盖身份。查询复用原订单 Service / Repository，WHERE 同时限定用户与订单号；他人订单与不存在订单统一 not_found。物流只有明确教学模拟说明，无外部物流服务。
- 原工具 schema 转为供应商格式后可能精简 additionalProperties，因此本地 Pydantic 校验不可省略；未知工具、夹带 user_id、非法参数不执行查询。无效 JSON / ID、多个调用超预算先阻止；第二轮再请求工具也不执行。ToolMessage 使用原调用 ID 与原 assistant 调用一起回传。
- 真实模式使用已选 DeepSeek 工厂与 bind_tools；模拟模式只固定查询 DEMO-A001，不理解任意问题，模型请求计数为零，订单卡片仍来自当前用户真实教学 MySQL。最终模型文字需与确定性卡片核对，不能当作事实保证。不展示模型私有思考链。
- 没有新增依赖、表、迁移或环境字段。新增 schemas / Service / AI tools / AI models / API 模块，前端按组件 / composable / API / types 拆分。讲义 docs/lessons/Q12-tool-calling.md 提供调用链、逐行断点、30 秒面试回答与失败实验。
- 验证：最终98项后端通过（真实MySQL与两种真实适配器内存协议，含非对象参数安全错误）；83个Python文件格式检查通过，5项前端测试、Prettier、TypeScript/Vite通过，仅有原包体提示。没有调用付费模型，真实模型选工具/澄清行为待用户验收。
- 浏览器在独立8001/5174模拟服务验证模型提议 → 工具执行 → 结果答复轨迹、调用ID、参数和MySQL卡片；375px下页面宽度无横向溢出。截图 runtime/Q12-order-tools.png 已忽略，临时服务已停止，未操作用户IDEA8000/5173。实验只读，不创建会话或订单。
- 原有 Q02 讲义和 docs/面试.md 继续保留，不混入提交。下一步用户重新 Debug backend/run.py，刷新后打开“订单工具实验”，按Q12讲义观察tool_calls、参数校验、短数据库会话和ToolMessage。理解后直接Q13 create_agent；规则检索工具可选，不强制回到RAG。
