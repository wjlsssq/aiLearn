"""IDEA 本地调试入口：右键此文件选择 Debug，即可调试完整 HTTP 请求。"""

from pathlib import Path  # 从启动文件定位仓库，不依赖 IDE 的工作目录推断。
import asyncio  # 使用 Python 自带的 Runner 管理事件循环生命周期。
import sys  # 启动时为完整的 backend 包提供模块查找路径。
import uvicorn  # 在当前调试进程运行 ASGI 应用。


def main(port: int = 8000) -> None:  # 入口只负责启动；可指定端口进行独立启动验证。
    project_root = (
        Path(__file__).resolve().parent.parent
    )  # backend 的上一级为仓库根目录。
    if (
        str(project_root) not in sys.path
    ):  # IDEA 直接执行脚本时，默认只加入 backend 目录。
        sys.path.insert(0, str(project_root))  # 仅在启动入口建立完整包的查找上下文。
    config = uvicorn.Config(  # 显式装配服务，便于控制异步启动方式。
        "backend.app.main:app",  # 以完整包名加载应用，保留相对导入的包上下文。
        host="127.0.0.1",  # 本机开发接口，与前端代理保持一致。
        port=port,  # 默认 8000，与前端的 /api 代理保持一致。
        loop="asyncio",  # 本机调试使用 Python 标准事件循环。
        reload=False,  # 调试期间关闭热重载，防止请求进入另一个子进程。
        workers=1,  # 所有请求由当前调试进程处理。
    )
    server = uvicorn.Server(config)  # 创建服务，尚未启动监听。
    with asyncio.Runner() as runner:  # 退出时关闭事件循环并回收异步资源。
        runner.run(server.serve())  # 绕开旧 pydevd 修改过的 asyncio.run 参数签名。


if __name__ == "__main__":  # 仅在执行启动文件时开启服务器。
    main()  # 导入该模块不会自动启动服务。
