# 代码规范与目录职责

这些约定来自用户要求：前端遵守 Prettier，前后端按清晰架构逐步扩展。根目录 `AGENTS.md` 是后续 Codex 修改代码必须读取和遵守的入口。

## 前端目录

```text
frontend/
  .prettierrc.json             # 唯一前端格式配置
  .prettierignore              # 排除依赖、产物和生成的锁文件
  src/
    App.vue                   # 装配页面，不存放业务流程
    main.ts                   # Vue、组件库与样式注册
    views/WorkbenchView.vue   # 页面布局和组件绑定
    components/workbench/     # 工作台展示组件
      SessionSidebar.vue
      LoginForm.vue
      ChatPanel.vue
      OrderPanel.vue
    composables/useWorkbench.ts # 响应式状态和业务操作
    api/                      # client.ts + auth/chat/order/health 接口
    types/api.ts              # 前后端共享的数据契约类型
    utils/auth-storage.ts     # 无 UI 依赖的凭据存储工具
    styles/workbench.css      # 格式化后的全局和工作台样式
```

数据流：用户触发组件事件 → 页面绑定 composable 操作 → 业务 API → 公共 HTTP 客户端 → 后端。请求结果由 composable 更新状态，再通过 props 传给组件。

组件使用 props、emits 和明确的 v-model 契约协作，不修改父级传入的 props。API 模块声明具体返回类型，不操作 Vue 状态或弹出提示。`api/client.ts` 只处理公共 HTTP 行为，避免把认证页面逻辑放进请求封装。

Vue 组件使用 PascalCase 命名；页面以 View 结尾；composable 以 use 开头；其他文件按业务命名。只为已有功能建立文件，禁止为了凑结构预建大量空页面。

## 后端目录

```text
backend/app/
  main.py                     # 创建应用、注册路由、映射业务异常
  api/
    router.py                 # 聚合业务路由与 /api 前缀
    dependencies.py           # Bearer 凭据到认证用户的 HTTP 适配
    routes/                   # auth/chat/order/health 路由
  schemas/                    # 请求与响应 Pydantic DTO
  services/                   # 业务规则、用户归属检查、事务边界
  repositories/               # SQL 查询、实体新增和必要的 flush
  models/entities.py          # ORM 实体与字段约束
  models/__init__.py          # 明确导出实体和注册元数据
  db/session.py               # 引擎、SessionLocal、Base、get_db
  core/config.py              # 从项目根目录定位 .env
  core/security.py            # 密码算法和令牌摘要
  core/errors.py              # 业务异常类型
  ai/models/factory.py        # 供应商模型工厂和配置校验
  ai/models/gateway.py        # 单次模型调用、统一结果和外部错误边界
  ai/prompts/customer_service.py # 版本化客服模板与变量
  ai/chains/customer_service.py  # Q03 固定 LCEL 链与请求内步骤观察器
```

依赖方向：API → Service → Repository → ORM / DB。API 负责 HTTP 参数与响应契约；Service 负责业务决定和提交；Repository 负责执行 SQL，不导入 FastAPI，不自行提交事务；ORM 实体不导入路由。

会话读取与写入共用 Service 中的归属检查，Repository 在 SQL 中同时限定会话 ID 与用户 ID。问答和新会话保持在同一事务中。请求关闭时，数据库依赖负责回滚尚未提交的事务。

初始化脚本从 `core/security.py` 导入密码工具，避免为了复用一个函数而创建整套 Web 应用。以后增加实体时同步登记明确的实体导出入口和数据库迁移。

后续知识库模块按同一职责增加 `schemas/knowledge.py`、`services/knowledge.py`、`repositories/knowledge.py` 等；LangChain 实现放 `app/ai`，需要时再创建。禁止向 main.py 或单个页面继续堆叠新业务。

## 格式与验证命令

前端在 frontend 目录执行：

```powershell
# 根据 Prettier 配置整理所有手写前端文件。
npm.cmd run format
# 只检查，不写文件；不符合时返回非零退出码。
npm.cmd run format:check
# 检查 TypeScript 并构建前端。
npm.cmd run build
```

Prettier 统一两空格缩进、单引号、无分号、LF 换行、100 字符目标行宽及 Vue 属性换行。锁文件自动生成，格式化时排除。IDE 安装 Prettier 支持后，选择 `frontend/node_modules/prettier`，使用项目内配置，启用保存时格式化。

后端在项目根目录执行：

```powershell
# 检查 Python 文件格式。
uv run --locked ruff format --check backend scripts tests
# 验证真实 MySQL 下的认证、归属隔离、消息持久化和错误响应。
uv run --locked python -m pytest tests -q
```

Python 保持四空格缩进。教学注释继续解释实际语句、输入输出和事务边界；复杂表达式拆行，避免多个操作挤在一行。

`npm install` 必须在 E 盘实际依赖目录中运行，安装或升级后把 package.json 和 package-lock.json 同步回前端源码目录；重装依赖使用 `scripts/install_frontend.ps1`。`.idea` 属于本机配置，不进入版本库。


Q06 草稿模块：`schemas/draft.py` 定义字段与报告，`ai/prompts/draft.py` 生成提取消息，`ai/models/draft.py` 处理供应商结构化调用，`services/draft.py` 做来源与缺失项判断，`api/routes/draft.py` 提供认证接口；前端对应 `DraftLab.vue`、`useDraftLab.ts`、`api/draft.ts`、`types/draft.ts`。本阶段不持久化，不为草稿创建空 Repository 或数据库表。


Q07 知识模块：`schemas/knowledge.py` 定义契约，`ai/rag/splitter.py` 只做规范化与切分，`services/knowledge.py` 管理归属、版本与事务，`repositories/knowledge.py` 管理查询及锁，`models/knowledge.py` 定义三张知识表。数据库增量变更放 `backend/migrations/versions`，通过 `backend/alembic.ini` 运行；原五张表保留初始化基线。前端使用 `components/knowledge`、`useKnowledge.ts`、`api/knowledge.ts`、`types/knowledge.ts`，由 WorkbenchView 组合，不在组件里发 HTTP。合成规则样例放 `datasets/shop-rules-demo.md`。
