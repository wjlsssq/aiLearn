"""独立空库验证旧基线与当前 ORM 基线都可以升级，不操作业务库。"""

import os
import re
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text

from backend.app.db.session import Base, url
from backend.app.models import AccessToken, ChatMessage, ChatSession, Order, User


@pytest.mark.parametrize("current_baseline", [False, True])
def test_agent_migration_accepts_old_and_fresh_baseline(current_baseline):
    name = "shopmind_migration_test_" + uuid.uuid4().hex[:10]
    assert re.fullmatch(r"shopmind_migration_test_[a-f0-9]{10}", name)
    server = create_engine(url.set(database=None))
    target = create_engine(url.set(database=name))
    created = False
    try:
        with server.begin() as db:
            db.execute(text(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4"))
        created = True
        Base.metadata.create_all(
            target,
            tables=[
                model.__table__
                for model in (User, AccessToken, Order, ChatSession, ChatMessage)
            ],
        )
        if not current_baseline:
            with target.begin() as db:
                db.execute(text("ALTER TABLE chat_messages DROP COLUMN artifacts"))
        if not current_baseline:
            from backend.app.schemas.order import OrderResponse

            legacy = {"order_no", "product", "status"}
            with target.begin() as db:
                for column in set(OrderResponse.model_fields) - legacy:
                    db.execute(text(f"ALTER TABLE orders DROP COLUMN `{column}`"))
        environment = {**os.environ, "DB_NAME": name}
        for _ in range(2):
            process = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "alembic",
                    "-c",
                    "backend/alembic.ini",
                    "upgrade",
                    "head",
                ],
                env=environment,
                check=False,
                capture_output=True,
            )
            assert process.returncode == 0, process.stderr.decode(
                "utf-8", errors="replace"
            )
        schema = inspect(target)
        assert "agent_order_data" in schema.get_view_names()
        assert "agent_query_audits" in schema.get_table_names()
        assert any(
            column["name"] == "artifacts" and column["nullable"]
            for column in schema.get_columns("chat_messages")
        )
        with target.connect() as db:
            assert (
                db.scalar(text("SELECT version_num FROM alembic_version"))
                == "0003_order_details"
            )
    finally:
        target.dispose()
        if created:
            assert re.fullmatch(r"shopmind_migration_test_[a-f0-9]{10}", name)
            with server.begin() as db:
                db.execute(text(f"DROP DATABASE `{name}`"))
        server.dispose()
