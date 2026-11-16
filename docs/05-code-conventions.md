# ShopMind 代码架构与产品约定

以根目录 AGENTS.md 为约束。业务界面服务实际工作流，中文注释与独立文档解释实现；不把教学实验、技术参数、假统计塞进产品页面。

## 前端结构

- `App.vue`：中文组件配置与页面入口。`main.ts` 只注册实际使用的 Element Plus 组件。
- `views/WorkbenchView.vue`：业务导航、会话布局及抽屉组合。`OrdersView.vue` / `KnowledgeView.vue` 组合订单与资料页面。
- `components/workbench`：登录、会话列表、消息区和订单上下文；`components/agent`：订单助手；`components/after-sales`：售后资料；`components/common`：一致的图标。
- `composables`：useWorkbench 负责会话生命周期；useOrderAssistant / useAfterSalesDraft / useKnowledge 分别管理业务请求状态、身份变化和旧响应拒收。
- `api/client.ts`：认证头、错误转换、204 和流读取。按业务域的 API 文件不访问组件状态。
- `types`：请求响应契约；`utils`：凭据存储和纯 SSE 解析。
- `styles`：theme / app-shell / conversations / resources / login 各司其职，workbench.css 聚合并放响应式规则。

组件通过 props/emits 协作，不直接发 HTTP。所有手写 Vue/TS/CSS/JSON 运行项目 Prettier；修改后执行 format:check 和 build。依赖通过 scripts/install_frontend.ps1 安装到 E 盘，不在源码目录 npm install。

## 后端结构

API 只适配 HTTP，Service 决定身份、业务规则与事务，Repository 写参数化 SQL，ORM/DB 定义实体和连接。业务异常在 main.py 统一映射为 HTTP；不得反向导入应用入口获得配置。

- `api/routes/auth.py`：login / me / logout；退出只撤销当前令牌。
- `api/routes/assistant.py`：面向产品的订单助手，结果不暴露工具 schema 或轨迹。
- `services/assistant.py` 直接组织业务响应，保留工具白名单、预算和严格参数校验，不再包装实验轨迹服务。
- `ai/tools/order.py` 接收服务层注入的查询回调，工具参数中不包含 user_id。Repository 查询必须同时限定用户与订单编号。
- `services/chat.py` 管理会话归属和成对写入；AI 网关只处理模型协议，数据库事务不跨模型等待。
- `services/draft.py` 保留字段与来源检查，草稿不等于工单；服务未启用时不返回固定演示结果。
- `services/knowledge.py` 管理私有文档与版本，切分由 ai/rag/splitter.py 内部完成；接口不再提供教学样例或分块 A/B 预览。
- 新表与改表经 `backend/migrations` / `backend/alembic.ini` 管理，原五张表仅保留初始化基线。
- `scripts/seed_business_data.py` 只用于本地开发样本追加，默认预览；批量用户和订单在同一事务写入，不作为 HTTP 产品接口，运行数据和凭据仅存忽略目录。用法见 [业务数据](10-business-data.md)。
- `database/snapshots` 存放用户明确授权提交的开发库全量 SQL，`database/README.md` 说明恢复和验证；`scripts/export_database.py` 调用原生 mysqldump 更新快照，不自动导入或覆盖现有库。其他运行数据和明文凭据仍不提交。

## 验证与交接

必须验证真实 MySQL、认证和数据归属；模型测试使用内存 HTTP 传输验证真实适配器，不消耗付费额度。SSE 测试检查中文跨字节、合并帧和截断。UI 验收在独立端口运行，临时替身与日志不提交，原有服务不被重启。

修改前 git status → git pull --ff-only → 读 AGENTS.md / 交接；完成后更新交接、检查暂存区、提交并推送。环境、密钥、IDE、依赖、缓存和运行产物不得提交。用户原有未提交笔记保留。
