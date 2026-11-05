# 阶段 0：Python 3.12 项目环境

准备日期：2026-11-05。项目源码目录：`C:\Users\27959\Desktop\ailearn`。Python 运行环境统一存放在 `E:\ailearn-runtime\shopmind`。

## 1. 当前环境

| 项目 | 结果 |
| --- | --- |
| Python | CPython 3.12.13，Windows x64 |
| 解释器真实位置 | `E:\ailearn-runtime\shopmind\tools\python\cpython-3.12.13-windows-x86_64-none\python.exe` |
| 虚拟环境真实位置 | `E:\ailearn-runtime\shopmind\venv` |
| 项目解释器入口 | `.venv\Scripts\python.exe`，经目录联接访问 E 盘 |
| 环境与依赖管理 | 本机已有 uv 0.11.1 |
| 包下载源 | PyPI：`https://pypi.org/simple` |
| 精确依赖版本 | 根目录 `uv.lock` |
| 依赖缓存真实位置 | `E:\ailearn-runtime\shopmind\cache\uv` |

解释器由 uv 从 Astral 官方 `python-build-standalone` 发行源下载，使用本机 uv 发行清单中的 3.12.13。按用户的磁盘安排，解释器和缓存已迁到 E 盘，虚拟环境在 E 盘依据原有锁文件重新创建。系统 PATH、注册表和原有 Python 3.8.6 均未修改。

项目中的 `.tools`、`.cache`、`.venv` 是 Windows 目录联接（Junction），分别指向 E 盘的 `tools`、`cache`、`venv`。它们保留原来的命令入口，文件数据存放在 E 盘。后续通过 `uv add`、`uv sync` 安装的依赖和缓存也使用这些 E 盘目录。

uv 的托管解释器说明见 [官方文档](https://docs.astral.sh/uv/guides/install-python/)。

## 2. 用 Java 概念理解这些文件

| Python 项目内容 | 可以怎样理解 |
| --- | --- |
| `.tools/python` | 指向 E 盘的项目 Python 运行时，作用类似为项目选定一个 JDK |
| `.venv` | 指向 E 盘的虚拟环境，隔离当前项目的解释器入口和第三方依赖 |
| `pyproject.toml` | 声明项目元信息、Python 版本范围、直接依赖和工具配置，部分作用类似 pom.xml |
| `uv.lock` | 固定直接依赖与传递依赖的实际版本、来源和文件校验信息 |
| `.python-version` | 告诉工具当前项目选用 Python 3.12.13 |
| `uv sync --locked` | 按现有锁文件同步环境；声明与锁文件不一致时明确报错 |

E 盘的 `venv` 依赖同一运行目录中 `tools/python` 的基础解释器，因此这两个目录都需要保留；迁移电脑时通过下方步骤重新创建，不直接复制虚拟环境。[Python 官方关于虚拟环境迁移的说明](https://docs.python.org/3.12/library/venv.html)。

## 3. 现在怎么运行 Python

在 PowerShell 中进入项目根目录：

```powershell
# 后续命令都在这个项目目录执行。
Set-Location 'C:\Users\27959\Desktop\ailearn'

# 通过项目入口使用 E 盘的 Python，避开系统命令入口冲突。
& '.\.venv\Scripts\python.exe' --version

# 检查解释器、虚拟环境、基础依赖和当前 Agent API。
& '.\.venv\Scripts\python.exe' '.\scripts\check_environment.py'
```

也可以交给 uv 自动选择项目虚拟环境：

```powershell
# 按锁定环境运行 Python，并显示版本。
uv run --locked python --version

# 使用同一个环境执行检查脚本。
uv run --locked python scripts/check_environment.py
```

如果希望在当前终端直接输入 `python`，可以激活：

```powershell
# 仅在当前 PowerShell 会话中优先使用项目解释器。
.\.venv\Scripts\Activate.ps1

# 激活后，这个命令应输出 Python 3.12.13。
python --version

# 结束当前虚拟环境的激活状态。
deactivate
```

如果本机 PowerShell 策略阻止执行激活脚本，使用前面的完整解释器路径或 `uv run` 即可。

## 4. 基础依赖

已安装 FastAPI、Uvicorn、LangChain、Pydantic Settings、SQLAlchemy、Alembic、PyMySQL、Cryptography，以及开发工具 pytest、httpx。LangGraph 随 LangChain 的依赖链安装。

Q01 已添加 langchain-deepseek、langchain-openai 和 openai，用于模型适配与 SDK 对照。环境检查本身不需要 API Key，也不会发起模型调用。

```powershell
# 查看项目环境中所有实际安装的包。
uv pip list --python '.\.venv\Scripts\python.exe'

# 检查包之间是否存在缺失或不满足的依赖要求。
uv pip check --python '.\.venv\Scripts\python.exe'

# 根据已提交的锁文件同步基础依赖。
uv sync --locked
```

依赖通过 uv 管理。后续添加直接依赖使用 `uv add 包名`，开发依赖使用 `uv add --dev 包名`，并同时维护 `pyproject.toml` 和 `uv.lock`。仅在需要升级时执行相应升级命令，避免无意改变课程运行环境。

## 5. 新电脑或重新准备环境

前提：Windows x64、可用的 uv、可访问官方发行源和 PyPI。先准备 E 盘目录，再安装解释器和环境。以下步骤用于新环境；若项目已有普通 `.venv` 等目录，应先核对并迁移，不直接覆盖。

```powershell
# 统一指定 E 盘的运行目录，变量只用于当前会话。
$taskRuntimeRoot = 'E:\ailearn-runtime\shopmind'

# 准备解释器与缓存的真实目录。
New-Item -ItemType Directory -Path "$taskRuntimeRoot\tools\python", "$taskRuntimeRoot\cache\uv" -Force

# 下载固定版本，不创建全局入口，也不注册到 Windows。
uv python install 3.12.13 --install-dir "$taskRuntimeRoot\tools\python" --no-bin --no-registry --cache-dir "$taskRuntimeRoot\cache\uv"

# 仅在尚未创建虚拟环境时执行，在 E 盘建立环境。
if (-not (Test-Path -LiteralPath "$taskRuntimeRoot\venv\pyvenv.cfg")) {
    uv venv --python "$taskRuntimeRoot\tools\python\cpython-3.12.13-windows-x86_64-none\python.exe" "$taskRuntimeRoot\venv" --cache-dir "$taskRuntimeRoot\cache\uv"
}

# 新项目创建目录联接；现有联接可跳过这三条命令。
New-Item -ItemType Junction -Path '.tools' -Target "$taskRuntimeRoot\tools"
New-Item -ItemType Junction -Path '.cache' -Target "$taskRuntimeRoot\cache"
New-Item -ItemType Junction -Path '.venv' -Target "$taskRuntimeRoot\venv"

# 通过项目入口同步环境，依赖和缓存实际写入 E 盘。
uv sync --locked --python '.\.tools\python\cpython-3.12.13-windows-x86_64-none\python.exe'

# 验证环境是否完整。
& '.\.venv\Scripts\python.exe' '.\scripts\check_environment.py'
```

`.tools`、`.venv`、`.cache` 已加入 `.gitignore`；`pyproject.toml`、`uv.lock`、`.python-version` 和检查脚本应随代码保留。`uv.lock` 是自动生成文件，不手工逐行修改。

## 6. 已完成的验证

- 项目入口输出 Python 3.12.13，检查脚本解析目录联接后，确认解释器与虚拟环境的真实位置在 E 盘。
- 基础依赖可以导入，`langchain.agents.create_agent` 可用。
- `uv pip check` 检查了 60 个已安装包，依赖兼容性通过。
- `uv run --locked --offline python --version` 成功，说明现有锁定环境可离线运行。
- 使用临时 FastAPI 应用完成一次 TestClient 请求，状态码与 JSON 响应正确；临时应用没有写入项目接口。
- SQLAlchemy 可以正确加载 MySQL + PyMySQL 方言，本次未连接数据库。

实际版本包括：FastAPI 0.162.0、LangChain 1.4.9、LangGraph 1.2.20、SQLAlchemy 2.1.8、PyMySQL 1.2.3。完整版本以 `uv.lock` 和环境检查输出为准。

Codex 的 Windows 受限沙箱内，asyncio 初始化本机 socketpair 时出现阻塞；同样的 FastAPI 检查在沙箱外立即通过。后续在 Codex 中运行异步服务器或相关测试时，需要考虑这一执行环境限制。

E 盘不在本聊天的默认可写工作区内，Codex 对 E 盘执行安装、缓存更新等写入时需要通过工具权限审核；普通本机 PowerShell 可直接使用上面的命令。

## 7. 本阶段的范围

本阶段只准备 Python 环境和基础依赖。MySQL 账号已在此前通过只读查询验证，本次未创建业务数据库或应用接口。下一步搭建 Vue + FastAPI + MySQL 最小可运行骨架，再开始 Q01。
