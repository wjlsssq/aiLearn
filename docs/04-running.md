# 阶段 0：启动与验收

工作目录：`C:\Users\27959\Desktop\ailearn`。Python、前端依赖和 npm/uv 缓存实际位于 E 盘。

## 启动

项目已有本机 `.env`，数据库密码不会提交到版本库。其他机器先复制 `.env.example` 为 `.env`，填写 MySQL 连接配置。

第一个 PowerShell 终端，在项目根目录执行：

```powershell
# 幂等初始化独立教学库和合成数据，不清空已有数据。
uv run --locked python -m scripts.init_db
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

访问 [客服工作台](http://127.0.0.1:5173)。教学账号 `alice` 和 `bob`，密码均为 `Learn123!`。这是本机教学版本，使用合成订单与明确标识的模拟回复。

## 观察数据闭环

1. 登录 alice，看到 `DEMO-A001` 耳机订单。
2. 提问后出现明确的模拟回复，左侧新增会话。
3. 刷新页面，再点击左侧会话，从 MySQL 恢复消息。
4. 退出并登录 bob，看到 `DEMO-B001` 音箱订单，无法看到 alice 的会话。

数据库包含 users、access_tokens、orders、chat_sessions、chat_messages。密码保存加盐 scrypt 摘要；令牌保存 SHA256 摘要并设置到期时间。查询订单和会话始终附带认证用户归属条件。

本阶段通过显式 `create_all` 建立初始基线。它不会迁移已有字段；后续表结构变更会接入 Alembic，不能靠重复运行初始化脚本更新列定义。

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

从 `frontend/src/App.vue` 的 `send()` 开始，追踪请求至 `backend/app/main.py` 的 `chat()`，再观察 `get_db()` 如何注入数据库会话，以及 `ChatSession`、`ChatMessage` 如何映射表。

Java 对照：FastAPI 路由类似 Controller，Pydantic 请求类类似 DTO，Depends 类似依赖注入，SQLAlchemy Session 承载事务，模型类类似 Entity。这里先用少量文件看清请求闭环，后续课程再把 AI 调用和业务处理拆到 Service。

本课先理解：消息能保存到数据库，不代表模型已经拥有记忆。当前没有请求任何模型；Q01 将开始接入真实聊天模型，Q04 才进一步组织多轮上下文。

## 本次验收记录

- TypeScript 检查和 Vite 生产构建通过；全量 Element Plus 引入产生大包体提示，后续按页面拆分和按需引入优化。
- 真实 MySQL 集成检查通过，覆盖认证失败、订单隔离、会话跨用户读写拒绝、消息恢复和空白输入。
- 初始化脚本重复运行成功。
- 前端页面和 `/api/health` 代理均返回成功，浏览器完成登录、发送消息和查看模拟回答。
- npm 官方审计在类型工具升级后返回 0 个已知漏洞。
