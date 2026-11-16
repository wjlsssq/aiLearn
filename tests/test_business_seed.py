"""真实 MySQL 验证追加生成器的预览、幂等、冲突保护与整批回滚。"""

import json
import uuid
from dataclasses import replace

import pytest
from sqlalchemy import delete, select, update

from backend.app.core.security import verify_password
from backend.app.db.session import SessionLocal
from backend.app.models import Order, User
from scripts import seed_business_data as seed


@pytest.fixture
def dataset(tmp_path):
    config = seed.SeedConfig(
        dataset="t" + uuid.uuid4().hex[:8], users=12, orders=60, existing_user_orders=0
    )
    try:
        yield config, tmp_path / "credentials.json"
    finally:
        with SessionLocal.begin() as db:
            db.execute(
                delete(Order).where(
                    Order.order_no.startswith(config.order_prefix, autoescape=True)
                )
            )
            db.execute(
                delete(User).where(
                    User.username.startswith(config.user_prefix, autoescape=True)
                )
            )


def snapshot(config):
    with SessionLocal() as db:
        users = list(
            db.execute(
                select(User.username, User.password_hash)
                .where(User.username.startswith(config.user_prefix, autoescape=True))
                .order_by(User.username)
            )
        )
        orders = list(
            db.execute(
                select(Order.order_no, Order.user_id, Order.product, Order.status)
                .where(Order.order_no.startswith(config.order_prefix, autoescape=True))
                .order_by(Order.order_no)
            )
        )
        return users, orders


def test_plan_is_repeatable_and_contains_business_variation():
    config = seed.SeedConfig()
    names, orders = seed.build_plan(config)
    assert (names, orders) == seed.build_plan(config)
    assert len(names) == len(set(names)) == 1000
    assert len(orders) == len({order.order_no for order in orders}) == 20000
    assert {order.status for order in orders} == set(seed.STATUSES)
    assert len({order.product for order in orders}) == 160
    assert sum(order.username == "alice" for order in orders) == 200
    assert sum(order.username == "bob" for order in orders) == 200
    assert not set(names[:100]) & {order.username for order in orders}
    assert max(map(len, (order.order_no for order in orders))) <= 32
    assert orders != seed.build_plan(replace(config, seed=1))[1]


def test_preview_writes_nothing(dataset):
    config, path = dataset
    report = seed.seed_data(config, credential_path=path)
    assert not report["applied"] and report["added"] == {"users": 12, "orders": 60}
    assert not path.exists() and snapshot(config) == ([], [])


def test_repeat_preserves_existing_data_and_distinct_password_salts(dataset):
    config, path = dataset
    first = seed.seed_data(config, apply=True, credential_path=path)
    rows = snapshot(config)
    second = seed.seed_data(config, apply=True, credential_path=path)
    assert first["added"] == {"users": 12, "orders": 60}
    assert second["added"] == {"users": 0, "orders": 0} and snapshot(config) == rows
    password = json.loads(path.read_text(encoding="utf-8"))["password"]
    assert len({stored.split(":")[0] for _, stored in rows[0]}) == 12
    assert verify_password(password, rows[0][0].password_hash)


def test_collision_never_overwrites_changed_order(dataset):
    config, path = dataset
    seed.seed_data(config, apply=True, credential_path=path)
    with SessionLocal.begin() as db:
        db.execute(
            update(Order)
            .where(Order.order_no == f"{config.order_prefix}00000001")
            .values(product="人工修改，必须保留")
        )
    before = snapshot(config)
    with pytest.raises(ValueError, match="冲突"):
        seed.seed_data(config, apply=True, credential_path=path)
    assert snapshot(config) == before


def test_failed_batch_rolls_back_users_and_orders(dataset, monkeypatch):
    config, path = dataset
    original = seed.insert_orders

    def fail(db, orders, user_ids):
        original(db, orders[:2], user_ids)
        raise RuntimeError("模拟后续批次失败")

    monkeypatch.setattr(seed, "insert_orders", fail)
    with pytest.raises(RuntimeError, match="后续批次"):
        seed.seed_data(config, apply=True, credential_path=path)
    assert snapshot(config) == ([], [])
