"""向本地开发 MySQL 追加可复现业务样本；默认预览，--apply 才实际写入。"""

import argparse
import json
import random
import re
import secrets
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, insert, select, text
from sqlalchemy.orm import Session

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal, engine
from backend.app.models import Order, User
from scripts.business_order_details import build_details

# 合成商品与订单明细共同生成，金额和生命周期由纯函数保证一致性。
PRODUCTS = (
    "无线降噪耳机",
    "开放式蓝牙耳机",
    "便携蓝牙音箱",
    "桌面音箱",
    "机械键盘",
    "无线鼠标",
    "人体工学鼠标",
    "桌面扩展坞",
    "65W 氮化镓充电器",
    "100W 多口充电器",
    "移动电源",
    "磁吸无线充电座",
    "USB-C 数据线",
    "HDMI 高清线",
    "笔记本电脑支架",
    "显示器挂灯",
    "27 英寸显示器",
    "便携显示屏",
    "高清摄像头",
    "USB 会议麦克风",
    "智能手表",
    "运动手环",
    "电子阅读器",
    "便携投影仪",
    "智能台灯",
    "床头夜灯",
    "空气净化器",
    "桌面加湿器",
    "手持吸尘器",
    "除螨仪",
    "电动牙刷",
    "冲牙器",
    "恒温电水壶",
    "便携咖啡机",
    "多功能电煮锅",
    "空气炸锅",
    "护眼学习灯",
    "智能插座",
    "Wi-Fi 路由器",
    "家庭监控摄像头",
)
VARIANTS = ("标准款", "升级款", "轻享款", "旗舰款")
STATUSES = (
    "待付款",
    "待发货",
    "已发货",
    "运输中",
    "派送中",
    "已签收",
    "已完成",
    "已取消",
    "售后中",
    "已退款",
)
STATUS_WEIGHTS = (8, 10, 12, 10, 5, 35, 10, 6, 3, 1)


@dataclass(frozen=True)
class SeedConfig:
    dataset: str = "biz"
    users: int = 1000
    orders: int = 20000
    seed: int = 20261116
    existing_user_orders: int = 200  # 给 alice、bob 各追加此数量，不修改原订单。

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9]{0,9}", self.dataset):
            raise ValueError("dataset 只能包含 1～10 位小写字母/数字，且以字母开头")
        if not 1 <= self.users <= 5000 or not 1 <= self.orders <= 200000:
            raise ValueError("用户数范围 1～5000，订单数范围 1～200000")
        if not 0 <= self.existing_user_orders <= self.orders // 2:
            raise ValueError("每个既有账号的样本数不能超过总订单数的一半")

    @property
    def user_prefix(self) -> str:
        return f"sim_{self.dataset}_"

    @property
    def order_prefix(self) -> str:
        return f"SIM-{self.dataset.upper()}-"


@dataclass(frozen=True)
class OrderSeed:
    order_no: str
    username: str
    product: str
    status: str


def build_plan(config: SeedConfig) -> tuple[list[str], list[OrderSeed]]:
    names = [f"{config.user_prefix}{index:06d}" for index in range(1, config.users + 1)]
    empty_count = config.users // 10  # 约 10% 新用户没有订单，覆盖真实空态。
    high_count = max(1, config.users // 20)  # 约 5% 高频买家承担约 30% 普通订单。
    high_buyers = names[-high_count:]
    ordinary_buyers = names[empty_count:-high_count] or high_buyers
    orders = []
    for index in range(1, config.orders + 1):
        rng = random.Random(f"shopmind-business-v1:{config.seed}:{index}")
        if index <= config.existing_user_orders:
            owner = "alice"
        elif index <= config.existing_user_orders * 2:
            owner = "bob"
        else:
            owner = rng.choice(high_buyers if rng.random() < 0.3 else ordinary_buyers)
        orders.append(
            OrderSeed(
                order_no=f"{config.order_prefix}{index:08d}",
                username=owner,
                product=f"{rng.choice(PRODUCTS)} · {rng.choice(VARIANTS)}",
                status=rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0],
            )
        )
    return names, orders


def check_target() -> None:
    if (
        settings.db_host not in {"127.0.0.1", "localhost", "::1"}
        or settings.db_name != "langchain_lab"
    ):
        raise ValueError("生成器只允许连接本地 langchain_lab 开发库")


def preflight(db: Session, names: list[str], orders: list[OrderSeed]):
    owners = sorted(set(names) | {order.username for order in orders})
    user_ids = dict(
        db.execute(
            select(User.username, User.id).where(User.username.in_(owners))
        ).all()
    )
    missing_anchors = (
        {order.username for order in orders} - set(names) - user_ids.keys()
    )
    if missing_anchors:
        raise ValueError(
            "请先初始化本地开发账号：" + ", ".join(sorted(missing_anchors))
        )
    # 显式查询目标编号；不使用 INSERT IGNORE 隐藏归属冲突，也不更新任何存量字段。
    existing = {}
    for offset in range(0, len(orders), 1000):
        numbers = [order.order_no for order in orders[offset : offset + 1000]]
        for row in db.execute(
            select(Order.order_no, Order.user_id, Order.product, Order.status).where(
                Order.order_no.in_(numbers)
            )
        ):
            existing[row.order_no] = (row.user_id, row.product, row.status)
    for order in orders:
        expected = (user_ids.get(order.username), order.product, order.status)
        if order.order_no in existing and existing[order.order_no] != expected:
            raise ValueError(
                f"订单 {order.order_no} 与生成计划冲突，未覆盖；请使用新的 dataset"
            )
    return (
        user_ids,
        [name for name in names if name not in user_ids],
        [order for order in orders if order.order_no not in existing],
    )


def read_or_create_password(path: Path) -> str:
    if path.exists():
        password = json.loads(path.read_text(encoding="utf-8"))["password"]
        if not isinstance(password, str) or len(password) < 16:
            raise ValueError("本机样本凭据文件无效，不覆盖已有文件")
        return password
    path.parent.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(18)  # 不使用公开固定密码，每个数据集本机随机生成。
    with path.open("x", encoding="utf-8") as output:
        json.dump(
            {"password": password}, output
        )  # 仅存于已忽略的 runtime，不输出到日志。
    return password


def counts(db: Session) -> dict[str, int]:
    return {
        "users": db.scalar(select(func.count()).select_from(User)),
        "orders": db.scalar(select(func.count()).select_from(Order)),
    }


def insert_orders(
    db: Session, orders: list[OrderSeed], user_ids: dict[str, int]
) -> None:
    for offset in range(0, len(orders), 1000):
        db.execute(
            insert(Order),
            [
                {
                    "order_no": order.order_no,
                    "user_id": user_ids[order.username],
                    "product": order.product,
                    "status": order.status,
                    **build_details(order.order_no, order.status, order.product),
                }
                for order in orders[offset : offset + 1000]
            ],
        )  # 分批发送 SQL，仍在同一个事务中，任意批失败全部回滚。


def seed_data(
    config: SeedConfig, *, apply: bool = False, credential_path: Path | None = None
) -> dict:
    check_target()
    names, orders = build_plan(config)
    path = (
        credential_path
        or PROJECT_ROOT / "runtime" / f"business-data-{config.dataset}.credentials.json"
    )
    # 同数据集同时运行时直接拒绝，避免双方都把同一批记录判定为缺失。
    lock_name = f"shopmind.seed.{config.dataset}"
    with engine.connect() as lock:
        acquired = lock.scalar(text("SELECT GET_LOCK(:name, 0)"), {"name": lock_name})
        lock.commit()
        if acquired != 1:
            raise ValueError("同一数据集的生成器正在运行，请等待其完成")
        try:
            with SessionLocal() as db:
                before = counts(db)
                _, missing_names, missing_orders = preflight(db, names, orders)
            summary = {
                "dataset": config.dataset,
                "applied": apply,
                "before": before,
                "planned": {"users": config.users, "orders": config.orders},
                "added": {"users": len(missing_names), "orders": len(missing_orders)},
                "status_distribution": dict(Counter(order.status for order in orders)),
                "sample_users": names[:2] + names[-2:],
                "credential_file": str(path),
            }
            if not apply:
                return summary  # 预览不创建密码文件，不插入账号或订单。
            password = read_or_create_password(path) if missing_names else None
            new_users = []
            for index, name in enumerate(missing_names, 1):
                new_users.append(
                    {
                        "username": name,
                        "password_hash": hash_password(password, secrets.token_hex(16)),
                    }
                )
                if index % 100 == 0:
                    print(f"已准备密码摘要：{index}/{len(missing_names)}", flush=True)
            with SessionLocal.begin() as db:
                # 哈希计算期间不持有业务事务，写入前重新检查，唯一约束再做最终保护。
                _, current_missing, pending_orders = preflight(db, names, orders)
                current_set = set(current_missing)
                pending_users = [
                    row for row in new_users if row["username"] in current_set
                ]
                if pending_users:
                    db.execute(insert(User), pending_users)
                user_ids = dict(
                    db.execute(
                        select(User.username, User.id).where(
                            User.username.in_(names + ["alice", "bob"])
                        )
                    ).all()
                )
                insert_orders(db, pending_orders, user_ids)
                summary["added"] = {
                    "users": len(pending_users),
                    "orders": len(pending_orders),
                }
                summary["after"] = counts(db)
            return summary  # 离开事务块、提交成功后，调用者才会收到成功结果。
        finally:
            lock.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            lock.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="写入本地 MySQL；不指定时只预览"
    )
    parser.add_argument("--dataset", default="biz")
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--orders", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--existing-user-orders", type=int, default=200)
    args = parser.parse_args()
    try:
        summary = seed_data(
            SeedConfig(
                args.dataset,
                args.users,
                args.orders,
                args.seed,
                args.existing_user_orders,
            ),
            apply=args.apply,
        )
    except ValueError as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.apply:
        report_path = (
            PROJECT_ROOT / "runtime" / f"business-data-{args.dataset}.report.json"
        )
        report_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
