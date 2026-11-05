# 在 IDEA 中启动与断点调试

## 为什么直接运行 chat.py 会失败

`app/api/routes/chat.py` 是完整应用的一部分。直接执行这个文件时，它作为 `__main__` 运行，Python 无法确定 `from ...db.session` 所属的父包，因此报 `attempted relative import with no known parent package`。

调试应从应用启动入口发起，然后让真实 HTTP 请求走到路由、Service 和 Repository。概念上类似启动 Spring Boot 应用后，再请求某个 Controller。

## 推荐：右键启动文件调试

项目已提供 `backend/run.py`，它会通过完整模块名加载 FastAPI 应用，并关闭热重载和多进程。

入口使用 `asyncio.Runner` 执行 `Server.serve()`，兼容旧版 JetBrains 调试器对 `asyncio.run` 的补丁。正常运行和 IDEA 调试都使用同一入口。

1. IDEA 中打开 `backend/run.py`。
2. 右键编辑区域，选择 **调试 / Debug 'run'**，或点击 `main()` 入口旁的调试菜单。
3. 运行配置的解释器选择 `E:\ailearn-runtime\shopmind\venv\Scripts\python.exe`。
4. 看到 `Uvicorn running on http://127.0.0.1:8000` 后，再从前端发送请求。

建议在 **运行 → 编辑配置** 中保存以下 Python 配置，命名为 `ShopMind 后端调试`：

| 配置项 | 内容 |
| --- | --- |
| 类型 | Python |
| 脚本路径 | `C:\Users\27959\Desktop\ailearn\backend\run.py` |
| Python 解释器 | `E:\ailearn-runtime\shopmind\venv\Scripts\python.exe` |
| 工作目录 | `C:\Users\27959\Desktop\ailearn` |
| 脚本参数 | 留空 |

以后顶部下拉框选择这个固定配置，然后点击绿色小虫图标。当前路由文件可以保持打开，断点仍然会命中；顶部不必保持“当前文件”。

如果 IDEA 底部还显示 Python 3.8，项目 SDK 和模块 SDK 也要统一切换到上述 3.12 虚拟环境，避免编辑器解析与实际运行使用不同解释器。

## 第一次断点练习

1. 在 `backend/app/services/chat.py` 的 `content = body.message.strip()` 左侧行号栏点击，出现红点。
2. 启动上述 Debug 配置。
3. 打开 `http://127.0.0.1:5173`，登录教学账号，点击“新建会话”，输入消息并发送。
4. IDEA 暂停时查看 `body.message`、`body.session_id`、`user_id`、`content`。
5. 默认 Windows 键位：F8 单步跳过，F7 单步进入，Shift+F8 跳出，F9 继续；自定义键位以调试菜单显示为准。

建议依次观察：`api/routes/chat.py` → `services/chat.py` → `repositories/chat.py` → 数据库提交 → JSON 响应 → 前端显示。

`repository.create_session(...)` 只在 `body.session_id is None` 时执行。若断点打在这里，应先在前端点击“新建会话”；继续已有会话会走另一个分支。

暂停时前端可能持续显示“发送中”，这表示请求正在等待当前调试线程继续。完成观察后按 F9；浏览器或代理也可能因暂停过久超时，必要时新建请求。

## 常见问题

- **端口占用**：结束之前的后端终端或 Run/Debug 实例，再启动 IDEA 调试。同一端口只保留一个后端服务。
- **红点不命中**：确认是 Debug 启动、断点未被静音，并检查请求是否进入断点所在分支；调试时保持单进程、关闭 reload。
- **修改代码没生效**：此入口为调试关闭了自动重载，修改后停止并重新 Debug。
- **前端访问失败**：前端仍需独立启动；在 frontend 目录运行 `npm.cmd run dev -- --port 5173 --strictPort`。
- **仅运行入口没暂停**：业务函数在收到 HTTP 请求时才执行。启动服务器后还要从前端或 API 文档发起请求。
- **进入 server.py 并报 loop_factory 错误**：旧版 pydevd 替换的 `asyncio.run` 不接受新版 Uvicorn 的 `loop_factory` 参数。使用更新后的 `backend/run.py`，完全停止原调试会话后重新 Debug。这里进入依赖文件通常是异常暂停，而非业务断点命中。
- **继续运行后仍立即报错**：异常不会因为点击“继续 / 恢复程序”自动修复。修复启动入口后需要停止旧进程，再重新启动调试。

没有上述调试器兼容问题时，也可创建 Python 模块运行配置：模块名 `uvicorn`，参数 `backend.app.main:app --host 127.0.0.1 --port 8000`，工作目录为仓库根目录，使用同一解释器。IDEA 2025.1 的调试建议优先选择项目提供的 `backend/run.py`。

错误的 `coroutine 'Server.serve' was never awaited` 警告是启动函数参数错误后的连带结果：协程已创建，但执行它的函数在参数校验阶段就失败了。

参考：[Uvicorn 同类调试问题](https://github.com/Kludex/uvicorn/issues/2737)、[Python Runner 生命周期](https://docs.python.org/3.12/library/asyncio-runner.html)。

参考：[JetBrains 运行/调试配置](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html)、[Uvicorn 启动设置](https://uvicorn.dev/settings/)。
