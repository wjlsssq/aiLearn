# 在 E 盘管理依赖，避免 npm 重建项目中的目录联接。
$ErrorActionPreference = 'Stop' # 文件操作失败时立即停止。
$taskProject = Split-Path -Parent $PSScriptRoot # 从脚本位置定位项目根目录。
$taskFrontend = Join-Path $taskProject 'frontend' # 前端源码仍放在项目内。
$taskDeps = 'E:\ailearn-runtime\shopmind\frontend-deps' # npm 的真实安装工作目录。
New-Item -ItemType Directory -Path $taskDeps -Force | Out-Null # 准备 E 盘目录。
Copy-Item -LiteralPath (Join-Path $taskFrontend 'package.json') -Destination $taskDeps # 同步依赖声明。
if (Test-Path -LiteralPath (Join-Path $taskFrontend 'package-lock.json')) { # 已有锁文件时使用精确安装。
    Copy-Item -LiteralPath (Join-Path $taskFrontend 'package-lock.json') -Destination $taskDeps # 同步锁文件。
}
Push-Location $taskDeps # npm 直接操作 E 盘的真实目录。
try { # 确保退出时恢复工作目录。
    npm.cmd ci --registry https://registry.npmjs.org --cache 'E:\ailearn-runtime\shopmind\cache\npm' # 使用已提交锁文件安装。
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' } # 不把安装失败当作成功。
} finally { Pop-Location } # 恢复用户当前目录。
$taskLink = Join-Path $taskFrontend 'node_modules' # 源码目录中的依赖入口。
if (-not (Test-Path -LiteralPath $taskLink)) { # 仅创建缺失入口，不覆盖已有目录。
    New-Item -ItemType Junction -Path $taskLink -Target (Join-Path $taskDeps 'node_modules') | Out-Null # 文件实际存放在 E 盘。
} elseif ((Get-Item -LiteralPath $taskLink).Target -ne (Join-Path $taskDeps 'node_modules')) { # 检查已有入口是否符合约定。
    throw 'Unexpected node_modules location; inspect it before continuing.' # 防止误改其他依赖目录。
}
