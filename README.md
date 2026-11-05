# ShopMind：用智能售后客服学习 LangChain

> aiLearn · 个人ai学习

面向有 Java 后端经验、Python 基础较少的学习者。目标是完成一个可演示的前后端项目，并能在面试中结合自己的实现解释 LangChain、RAG、Agent 和工程设计。

## 项目场景

用户问“这款耳机能七天无理由退货吗？”，客服从店铺规则中检索依据；用户接着问“那我的订单呢？”，客服查询当前用户的 MySQL 订单；用户申请售后时，系统生成草稿，等待用户确认后创建模拟售后工单。

所有订单、物流和售后均为教学模拟数据。

## 计划入口

- [双电脑交接与当前待办](docs/07-handoff.md)：每次修改前先拉取、阅读；完成后更新并随代码提交推送。
- [Q01：模型调用与 LangChain 的作用](docs/lessons/Q01-langchain-models.md)：DeepSeek 配置、断点、SDK 对照与面试练习。
- [Q02：Prompt 与消息角色](docs/lessons/Q02-prompt-messages.md)：店铺变量、风格切换、消息预览、模板版本和断点练习。
- [IDEA 启动与断点调试](docs/06-idea-debugging.md)：右键 backend/run.py 启动，逐步观察 HTTP 请求。
- [代码规范与目录职责](docs/05-code-conventions.md)：Prettier、后端格式与分层要求；后续修改还须遵守根目录 AGENTS.md。
- [项目启动与阶段 0 验收](docs/04-running.md)：登录、聊天、订单和测试命令。
- [Python 3.12 环境与使用方法](docs/00-environment.md)：解释器、虚拟环境、依赖和环境重建。
- [项目与学习计划](docs/01-project-plan.md)：技术栈、阶段安排、数据库、注释与教学规范。
- [20 道面试题与功能映射](docs/02-interview-map.md)：每题对应一个模块、验收案例和追问。
- [检索资料与版本依据](docs/03-references.md)：官方文档和公开面经，检索日期为 2026-11-05。

## 当前进度

- 已完成：场景选择、技术路线、20 个模块的递进计划和验收设计。
- 环境已准备：Python 3.12.13、虚拟环境和依赖缓存实际存放在 `E:\ailearn-runtime\shopmind`；根目录 `.venv` 等入口通过目录联接访问 E 盘，依赖版本保存在 `uv.lock`。
- 数据库已确认：两台电脑分别使用 MySQL 8.0.35 / 8.0.45；本机配置和恢复记录见交接文档。
- 阶段 0 已实现：Vue 工作台、FastAPI、MySQL、登录、订单隔离、会话历史和模拟聊天。
- Q01 已实现模型工厂、DeepSeek 调用和 SDK 对照脚本；真实模式由本机 .env 配置，真实服务验收与离线自动化测试分别记录。
- Q02 已实现版本化客服 Prompt、店铺名称与简洁/详细风格配置、无需模型请求的消息预览；预览与聊天使用相同渲染函数。真实调用及风格效果由用户在 IDEA 调试验收。
- 页面明确区分模拟与真实模式；本课仅把当前问题发送给模型，多轮上下文在 Q04 学习。

## 快速检查 Python 环境

在项目根目录的 PowerShell 中执行：

```powershell
# 使用项目虚拟环境，确认 Python 为 3.12.13。
& '.\.venv\Scripts\python.exe' --version

# 核实所有基础依赖和后续使用的 Agent API 可加载。
& '.\.venv\Scripts\python.exe' '.\scripts\check_environment.py'
```

每次推进一个主问题：先看功能，再讲概念与调用链，逐行读代码，做对照实验，最后练习面试表达。
