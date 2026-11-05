# ShopMind 项目约定

## 必须遵守的用户要求

- 两台电脑通过 GitHub `https://github.com/wjlsssq/aiLearn.git` 的 `main` 分支交接，持续维护 [交接文档](docs/07-handoff.md)。
- 每次开始修改前，先检查 `git status`，执行 `git pull --ff-only`，再阅读本文件和 `docs/07-handoff.md`；新聊天也必须遵守。若本机未提交修改导致无法拉取或分支分叉，先保留并核对差异，不强制覆盖、不自动重置或隐藏修改。
- 每次完成修改，更新交接文档的当前状态、验证结果、未完成事项和下一步，再将代码与文档一起提交并推送。用户已于 2026-11-05 明确授权此日常流程，无需每次重新询问。提交前核对敏感文件、测试和暂存内容；推送失败必须如实说明本地提交与远端状态。

- 交流、课程讲义和手写代码注释使用中文；教学核心语句按行解释用途、数据流和必要的设计原因。
- 前端所有手写 Vue、TypeScript、CSS、JSON 使用项目 Prettier 配置。修改后运行 `npm run format:check` 和 `npm run build`，禁止保留压缩成一行的源文件。
- 新文件必须放入下方约定的层次；先检查现有模块，禁止随意建目录、重复封装和把所有功能堆在入口文件。
- Python 解释器、虚拟环境、Python/npm 缓存和前端依赖放 E 盘。项目内 `.venv`、`.tools`、`.cache` 和 `frontend/node_modules` 为目录联接，不能用普通目录覆盖。
- 前端依赖通过 `scripts/install_frontend.ps1` 同步到 E 盘；新增依赖后同时同步前端 package.json、package-lock.json。不要在源码目录直接运行 npm install。
- 数据库使用 MySQL；不提交 `.env`、密钥、IDE 本机配置、依赖、缓存、运行数据或构建产物。

## 前端职责

- `src/views`：页面组合和布局，页面命名 `*View.vue`。
- `src/components/<业务域>`：展示与交互组件，使用 PascalCase 文件名，通过 props/emits 与外部协作。
- `src/composables`：响应式状态、用户操作和业务流程，命名 `use*.ts`。
- `src/api`：按业务域组织类型明确的接口调用；通用 HTTP 行为只放 `api/client.ts`。
- `src/types`：共享 DTO 和类型；`src/utils`：无 UI 依赖的小型工具；`src/styles`：全局样式与页面布局样式。
- `App.vue` 仅作为应用入口，组件不直接发 HTTP 请求，API 层不导入组件或操作页面状态。

## 后端职责

- `app/main.py`：应用创建、路由注册、异常处理注册。
- `app/api/routes`：HTTP 路由、请求响应 DTO 和依赖声明，不写 SQL 或业务事务。
- `app/api/dependencies.py`：认证和请求依赖。
- `app/schemas`：按业务域定义 Pydantic DTO；`app/services`：业务规则、归属检查与事务边界。
- `app/repositories`：SQLAlchemy 查询和持久化，不依赖 FastAPI 或决定 HTTP 状态。
- `app/models`：ORM 实体；`app/db`：数据库会话、实体基类；`app/core`：配置、异常和安全工具。
- 后续 LangChain、RAG、工具和图逻辑放 `app/ai` 的对应业务模块，需要时再建，不预建空壳。
- 依赖方向：API → Service → Repository → ORM/DB；业务异常交给应用统一映射为 HTTP，禁止反向依赖。
- 初始化脚本、测试及业务模块不能通过导入 `main.py` 来获得密码算法或配置。

## 验证和文档

- 重构保持现有 API、认证、归属隔离和事务行为；运行真实 MySQL 集成检查。
- 后端执行 `uv run --locked ruff format --check backend scripts tests`，需要整理时去掉 `--check`。
- 启动入口和目录变更同步更新 README、课程阅读路线及架构文档。
- 每次修改后的提交与推送遵守上方双电脑交接流程；禁止提交密钥和本机运行文件。
