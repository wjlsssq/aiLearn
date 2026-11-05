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

- 用户有 Java / 后端经验，Python 较少，当前基础代码已理解，开始 Q01。
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
- 用户已选择 DeepSeek。示例配置使用 `LLM_PROVIDER=deepseek`、`https://api.deepseek.com`、`deepseek-flash`；具体可用模型需以用户账号及供应商当前文档为准。

### 尚未验收

- 尚未完成本次交接的真实 DeepSeek 调用验收；当前本机已存在密钥配置，但有效性未验证。切换电脑后必须在自己的 `.env` 配置，不在聊天、文档或 Git 中传递密钥。
- Q01 自动化测试使用内存 HTTP 响应验证真实适配器，没有发起付费模型调用；不能将其描述为真实服务验收通过。
- 当前只把系统指令和本次问题发给模型。数据库保存历史不代表模型已经拥有记忆；多轮上下文在 Q04 实现。
- 尚未接入 RAG、订单工具、Agent、售后操作和流式输出。前端订单展示并不代表模型可查询订单。

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

按 [Q01 讲义](lessons/Q01-langchain-models.md) 继续：

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
