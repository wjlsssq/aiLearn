"""为本地 Agent 创建仅 SELECT 订单视图的账号，随机密码只写本机 .env。"""

import os
import re
import secrets
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, text

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.db.session import engine, url


def main():
    if (
        settings.db_host not in {"127.0.0.1", "localhost", "::1"}
        or settings.db_name != "langchain_lab"
    ):
        raise RuntimeError("此脚本仅用于本地 langchain_lab")
    username = "shopmind_agent_ro"
    path = PROJECT_ROOT / ".env"
    if not path.is_file():
        raise RuntimeError("请先准备本机 .env，再创建只读账号")
    password = settings.agent_db_password.get_secret_value()
    with engine.begin() as db:
        exists = db.scalar(
            text(
                "SELECT COUNT(*) FROM mysql.user WHERE User=:user AND Host='localhost'"
            ),
            {"user": username},
        )
        if exists and not password:
            raise RuntimeError(
                "只读账号已存在但本机没有对应密码；保留原账号，请核对 .env"
            )
        if not exists:
            password = password or secrets.token_urlsafe(24)
            db.execute(
                text(
                    "CREATE USER 'shopmind_agent_ro'@'localhost' IDENTIFIED BY :password"
                ),
                {"password": password},
            )
            db.execute(
                text(
                    "GRANT SELECT ON langchain_lab.agent_order_data TO 'shopmind_agent_ro'@'localhost'"
                )
            )
        grants = [
            row[0]
            for row in db.execute(
                text("SHOW GRANTS FOR 'shopmind_agent_ro'@'localhost'")
            )
        ]
        principal = "`shopmind_agent_ro`@`localhost`"
        expected = {
            f"GRANT USAGE ON *.* TO {principal}",
            f"GRANT SELECT ON `langchain_lab`.`agent_order_data` TO {principal}",
        }
        if set(grants) != expected:
            raise RuntimeError("只读账号权限与预期不符，未修改权限；请人工核对")
    check = create_engine(url.set(username=username, password=password))
    try:
        with check.connect() as db:
            db.execute(text("SELECT order_no FROM agent_order_data LIMIT 1"))
    finally:
        check.dispose()
    content = path.read_text(encoding="utf-8")
    for key, value in {
        "AGENT_DB_USER": username,
        "AGENT_DB_PASSWORD": password,
    }.items():
        expression = rf"(?m)^{key}=.*$"
        line = f"{key}={value}"
        content = (
            re.sub(expression, lambda _, replacement=line: replacement, content)
            if re.search(expression, content)
            else content.rstrip() + "\n" + line + "\n"
        )
    runtime = PROJECT_ROOT / "runtime"
    runtime.mkdir(exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix="agent-env-", suffix=".tmp", dir=runtime
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(content)
        Path(temporary).replace(
            path
        )  # 完整写入后再替换，避免失败时截断原有模型密钥配置。
    finally:
        Path(temporary).unlink(missing_ok=True)
    print("独立只读账号已验证，凭据仅保存于本机 .env；未授予基础表或写入权限。")


if __name__ == "__main__":
    main()
