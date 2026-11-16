# 项目启动与业务验收

工作目录：`C:\Users\27959\Desktop\ailearn`。Python、前端依赖和 npm/uv 缓存实际位于 E 盘。

## 启动

使用 IDEA 调试时可右键 `backend/run.py` 选择 Debug，详见 [IDEA 断点调试](06-idea-debugging.md)。下面为终端启动方式，两种方式选择一种运行后端。

项目已有本机 `.env`，数据库密码不会提交到版本库。其他机器先复制 `.env.example` 为 `.env`，填写 MySQL 连接配置。

第一个 PowerShell 终端，在项目根目录执行：

```powershell
# 幂等初始化独立教学库和合成数据，不清空已有数据。
uv run --locked python -m scripts.init_db
# Q07 起新增表使用迁移，老库与新库都要执行；不改变原有聊天数据。
uv run --locked alembic -c backend/alembic.ini upgrade head
# 运行后端，接口文档位于 http://127.0.0.1:8000/docs。
uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

第二个终端执行：

```powershell
# 切换到前端源码目录。
Set-Location 'C:\Users\27959\Desktop\ailearn\frontend'
# 启动前端，由 Vite 将 /api 请求代理到后端。
npm.cmd run dev -- --port 5173 --strictPort
```

访问 [服务工作空间](http://127.0.0.1:5173)。界面不再预填或展示开发账号。已有本地开发种子账号仍可登录，生产开户与权限管理需单独建设，不能把种子脚本用于真实开户。

智能功能需要根目录 `.env` 配置 `CHAT_MODE=llm` 与有效模型。仅有 mock 配置时，产品禁用智能操作，资料和历史仍可查看。

## 业务验收

1. 登录后进入会话工作台，搜索和恢复当前账号历史；发送消息逐段显示，停止/重试不重复追加用户问题。
2. 生成时保留下一条草稿，重新打开会话从 MySQL 恢复完整成功问答。
3. 在订单中心搜索订单；打开订单助手查询当前账号订单；无权访问与不存在订单均不暴露详情。
4. 在规则文档保存或更新资料，查阅当前及历史版本。此功能尚未连接自动检索问答。
5. 整理售后资料、补充缺失信息；结果仅供核对，不代表创建工单。
6. 退出后当前令牌失效，再次登录其他账号，不残留上一账号的数据。

数据库包含 users、access_tokens、orders、chat_sessions、chat_messages。密码保存加盐 scrypt 摘要；令牌保存 SHA256 摘要并设置到期时间。查询订单和会话始终附带认证用户归属条件。

阶段 0 通过显式 `create_all` 建立五张表的初始基线；Q07 已接入 Alembic，知识库新增三张表由迁移管理。`create_all` 不会迁移已有字段，不能靠重复运行初始化脚本更新列定义。

## 验证与依赖

```powershell
# 在项目根目录执行真实 MySQL 集成验证；只清理测试自己创建的数据。
uv run --locked python -m pytest tests -q
# 在 frontend 目录执行 TypeScript 检查与生产构建。
npm.cmd run build
```

需要重装前端依赖时，在项目根目录执行 `powershell -ExecutionPolicy Bypass -File scripts/install_frontend.ps1`。脚本从锁文件安装到 E 盘真实目录；不要直接在源码目录运行 npm install，以免 npm 替换 node_modules 目录联接。

前端开发代理只用于 Vite 开发服务器。生产环境需要为 `/api` 配置反向代理，当前尚未部署生产服务。

## 第一轮代码阅读

从 `frontend/src/composables/useWorkbench.ts` 的 `send()` 开始，追踪 `api/chat.ts` 和 `api/client.ts`，再进入 `backend/app/api/routes/chat.py` → `services/chat.py` → `repositories/chat.py`。观察 `db/session.py` 的 `get_db()` 如何注入数据库会话，以及 `models/entities.py` 中的 `ChatSession`、`ChatMessage` 如何映射表。

Java 对照：FastAPI 路由类似 Controller，Pydantic 请求类类似 DTO，Depends 类似依赖注入，SQLAlchemy Session 承载事务，模型类类似 Entity。Service 负责业务规则和事务，Repository 负责数据访问。具体职责见 [代码规范](05-code-conventions.md)。

普通聊天会从当前用户授权会话读取最近完整问答；新会话隔离，取消和失败问答不会进入后续上下文。订单助手目前独立执行有界工具流程，普通聊天尚未自动调度订单工具。

## 当前验收方式

后端回归使用真实 MySQL，模型通过内存 HTTP 或测试替身提供，检查权限、流式保存、取消、版本与工具执行预算。UI 在独立端口检查桌面与手机布局，不占用用户 IDEA 的 8000 服务；不在未经说明的情况下消耗真实模型额度。

最终执行结果和待验收事项以 [交接文档](07-handoff.md) 最新记录为准。生产构建已按需注册实际使用的 Element Plus 组件，无原全量注册造成的 JS 大包提示。
