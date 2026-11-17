# 智能客服工作空间

将会话、订单与服务资料放在同一工作台，面向实际售后服务流程持续构建 Agent 应用。

## 当前能力

- 统一聊天：Agent 按需求自动查询订单、做分组统计或整理售后资料，支持流式、停止、重试和历史恢复。
- 订单中心：当前账号订单列表和搜索，快捷操作将需求带回聊天。
- 业务结果：订单表格、售后资料卡片随完整问答一起保存，刷新可恢复。
- 规则文档：导入 UTF-8 文本，保存版本与查阅历史；自动检索引用尚未启用。
- 登录与退出：身份从服务端恢复；退出撤销当前令牌，保留其他设备登录。

产品页面只显示业务操作和结果。查询支持受约束的动态 SQL，使用独立只读账号，并强制限定当前用户；不开放整个数据库。完整团队权限、图流程恢复与审批仍在后续建设中，资料整理不代表创建工单。

## 开始运行

Python 3.12、虚拟环境、缓存与前端依赖统一位于 E 盘。新电脑先按 [环境恢复](docs/00-环境准备.md) 创建目录联接；每次修改前先拉取代码并读 [项目约定](AGENTS.md)、[交接文档](docs/07-双电脑开发交接.md)。

```powershell
uv sync --locked
# 仅本机没有 .env 时从 .env.example 复制，并填写数据库与模型配置。
# 新的本地开发库通过下面命令初始化，已有数据不会清空。
uv run --locked python -m scripts.init_db
uv run --locked alembic -c backend/alembic.ini upgrade head
# 本地开发库创建独立查询账号，随机密码只保存本机 .env。
uv run --locked python -m scripts.setup_agent_database
# 或在 IDEA 右键 backend/run.py 选择 Debug。
uv run --locked python backend/run.py
```

前端首次准备依赖，在根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/install_frontend.ps1`；随后在 `frontend` 执行 `npm.cmd run dev`，访问 `http://127.0.0.1:5173`。

产品智能功能要求 `CHAT_MODE=llm` 与有效模型配置。未启用时界面保留资料和历史查看，禁用智能操作；订单助手和资料提取接口返回 503，不伪造模拟业务结果。`mock` 仅供底层自动化回归，不是产品演示入口。

当前迁移版本为 `0003_order_details`。拉取后先同步依赖、升级数据库并配置查询账号，再重新启动后端；旧合成订单另运行 `uv run --locked python -m scripts.enrich_business_orders --apply` 补齐金额、时间和收货信息；查询凭据缺失时会明确失败，不回退到 root。统一聊天的能力、SQL 子集和断点路线见 [智能体与统一聊天](docs/lessons/Q13-智能体与统一聊天.md)。

`init_db` 是本地开发种子脚本，包含合成账号及订单，不作为生产开户方式。已有示例数据原样保留并保留其模拟标识；数据库实时变化不会随 Git 自动同步。用户要求的[全量 SQL 快照](database/README.md)已随代码保存，另一台电脑可以手动恢复完整结构和数据，无需重新生成同一批样本。

需要批量业务样本时，执行 `uv run --locked python -X utf8 -m scripts.seed_business_data --apply`，默认追加 1,000 个用户与 20,000 笔订单，相同参数可重复运行且不会覆盖已有记录。账号、分布和自定义数量见 [本地业务数据](docs/10-本地业务样本数据.md)。

## 目录与验证

后端遵循 API → Service → Repository → ORM/DB；AI 适配和工具放 `backend/app/ai`。前端页面组合在 views，组件按业务域划分，操作流程在 composables，HTTP 与 DTO 分别在 api/types。样式按主题、外壳、会话、资源、登录拆分。

```powershell
uv run --locked ruff format --check backend scripts tests
uv run --locked python -m pytest tests -q
# 以下在 frontend 执行。
npm.cmd run format:check
node --test tests/*.test.mjs
npm.cmd run build
```

- [产品设计与调研](docs/09-产品工作台设计与调研.md)：页面结构、参考来源、清理范围与能力边界。
- [代码架构](docs/05-代码架构与开发规范.md)、[启动说明](docs/04-项目启动与业务验收.md)、[IDEA 调试](docs/06-启动与断点调试.md)。
- [双电脑交接](docs/07-双电脑开发交接.md)：当前状态、验证和下一步。

## 研发资料

中文代码注释与课程资料继续供断点学习使用，产品不展示教学内容。原 LCEL、Prompt 预览、工具实验、分块 A/B 与对照脚本已退出运行代码，旧讲义涉及的这些入口可在 Git 历史 `b3bc15a` 查看；当前实现以本文和产品设计文档为准。用户要求继续 Agent 业务路线，不强制补学文档检索。
