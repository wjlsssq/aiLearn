"""通过 MySQL 原生工具导出本地开发库全量快照，连接凭据不进入参数或 SQL。"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.app.core.config import PROJECT_ROOT, settings

DEFAULT_OUTPUT = PROJECT_ROOT / "database" / "snapshots" / "langchain_lab.sql"


def export_database(
    output: Path = DEFAULT_OUTPUT, executable: str = "mysqldump"
) -> dict:
    if (
        settings.db_host not in {"127.0.0.1", "localhost", "::1"}
        or settings.db_name != "langchain_lab"
    ):
        raise ValueError("只允许导出本地 langchain_lab 开发库")
    binary = shutil.which(executable)
    if not binary:
        raise ValueError(
            "未找到 mysqldump，请安装 MySQL 8 客户端或通过 --mysqldump 指定路径"
        )
    output = output.resolve()
    if output.suffix.lower() != ".sql":
        raise ValueError("导出路径必须是 .sql 文件")
    runtime = PROJECT_ROOT / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix="mysql-export-", suffix=".sql", dir=runtime
    )
    os.close(descriptor)  # MySQL 自己写文件，避开 PowerShell 重定向导致的编码变化。
    temporary_path = Path(temporary)
    try:
        environment = os.environ.copy()
        environment["MYSQL_PWD"] = (
            settings.db_password
        )  # 只传给子进程，不打印或写入 Git。
        subprocess.run(
            [
                binary,
                "--protocol=TCP",
                f"--host={settings.db_host}",
                f"--port={settings.db_port}",
                f"--user={settings.db_user}",
                "--default-character-set=utf8mb4",
                "--single-transaction",
                "--quick",
                "--skip-lock-tables",
                "--skip-add-locks",
                "--no-autocommit",  # 恢复时每张表批量提交，避免两万次逐行落盘。
                "--routines",
                "--events",
                "--triggers",
                "--hex-blob",
                "--no-tablespaces",
                "--set-gtid-purged=OFF",
                "--column-statistics=0",
                "--skip-comments",
                "--skip-dump-date",
                "--complete-insert",
                "--skip-extended-insert",
                f"--result-file={temporary_path}",
                settings.db_name,
            ],
            env=environment,
            check=True,
            capture_output=True,
        )
        sql = (
            temporary_path.read_bytes().rstrip(b"\r\n") + b"\n"
        )  # 统一文件末尾，便于 Git 检查。
        # 全量保留身份摘要；明文供应商密钥不属于应提交的业务数据。
        key = settings.llm_api_key.get_secret_value()
        if (len(key) >= 8 and key.encode() in sql) or re.search(
            rb"sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            sql,
        ):
            raise ValueError("SQL 中发现疑似明文密钥，未更新共享快照")
        if not sql.strip() or b"CREATE TABLE" not in sql:
            raise ValueError("导出结果缺少表结构，未更新共享快照")
        temporary_path.write_bytes(sql)
        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary_path, output)  # 导出成功且检查通过后才替换旧快照。
        return {
            "output": str(output),
            "bytes": len(sql),
            "sha256": hashlib.sha256(sql).hexdigest(),
        }
    finally:
        temporary_path.unlink(missing_ok=True)  # 清理本脚本创建的单个临时文件。


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mysqldump", default="mysqldump")
    args = parser.parse_args()
    try:
        result = export_database(args.output, args.mysqldump)
    except subprocess.CalledProcessError:
        parser.exit(1, "mysqldump 导出失败，请核对本机连接和导出权限；未替换旧快照。\n")
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
