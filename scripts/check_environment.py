"""检查本项目的解释器、虚拟环境和基础依赖；不会调用模型或连接数据库。"""

from importlib import import_module  # 动态导入模块，确认对应依赖确实能够加载。
from importlib.metadata import version  # 读取已安装发行包的真实版本。
from pathlib import Path  # 使用跨平台路径对象定位项目目录。
import sys  # 获取当前进程使用的解释器和 Python 版本。


def main() -> None:  # 检查没有业务返回值；失败时抛出异常并以非零状态退出。
    project_root = Path(__file__).resolve().parents[1]  # 从 scripts 目录向上定位仓库根目录。
    expected_venv = project_root / ".venv"  # .venv 是项目入口，目录联接指向 E 盘的真实环境。
    if sys.version_info[:2] != (3, 12):  # 比较主次版本，防止误用系统 Python 3.8。
        raise RuntimeError("Expected Python 3.12; use .venv/Scripts/python.exe.")  # 明确提示正确入口。
    if Path(sys.prefix).resolve() != expected_venv.resolve():  # 解析目录联接后比较真实位置，核实项目环境。
        raise RuntimeError("Expected the project's .venv virtual environment.")  # 防止把依赖装到其他环境。
    packages = {  # 左侧是发行包名，右侧是可导入的 Python 模块名，两者可能不同。
        "fastapi": "fastapi",  # 检查 HTTP 框架。
        "uvicorn": "uvicorn",  # 检查后端运行服务器。
        "langchain": "langchain",  # 检查 LangChain 主包。
        "langgraph": "langgraph",  # 检查 LangChain 引入的图运行组件。
        "pydantic-settings": "pydantic_settings",  # 检查配置读取组件，模块名使用下划线。
        "SQLAlchemy": "sqlalchemy",  # 检查 ORM 和数据库工具。
        "alembic": "alembic",  # 检查数据库迁移工具。
        "PyMySQL": "pymysql",  # 检查 MySQL 驱动。
        "cryptography": "cryptography",  # 检查加密组件。
        "pytest": "pytest",  # 检查测试工具。
        "httpx": "httpx",  # 检查 HTTP 客户端。
    }
    print(f"Python: {sys.version.split()[0]}")  # 打印实际解释器版本，便于核对环境。
    print(f"Executable: {sys.executable}")  # 打印实际运行路径，便于排查命令入口问题。
    print(f"Physical executable: {Path(sys.executable).resolve()}")  # 打印 E 盘的真实文件位置。
    print(f"Base Python: {sys.base_prefix}")  # 确认基础解释器也使用 E 盘安装。
    for distribution, module_name in packages.items():  # 依次验证每个基础依赖。
        import_module(module_name)  # 真正加载模块，缺失或不兼容时立即失败。
        print(f"{distribution}: {version(distribution)}")  # 输出锁定后实际安装的版本。
    from langchain.agents import create_agent  # 验证后续课程要使用的当前 Agent 入口。
    if not callable(create_agent):  # 检查导入对象确实可以作为函数调用。
        raise RuntimeError("LangChain create_agent is unavailable.")  # 接口不符合预期时明确失败。
    print("Environment check passed.")  # 所有环境检查完成后输出成功标记。


if __name__ == "__main__":  # 直接执行本文件时运行检查，被导入时不产生检查副作用。
    main()  # 调用环境检查入口。
