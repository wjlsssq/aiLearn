"""为旧合成订单补齐明细；默认预览，--apply 写入，只允许本地开发库。"""

import argparse

from sqlalchemy import or_, select

from backend.app.db.session import SessionLocal
from backend.app.models import Order
from scripts.business_order_details import build_details
from scripts.seed_business_data import check_target


def enrich(*, apply: bool = False) -> dict:
    check_target()
    changed, skipped = 0, 0
    with SessionLocal.begin() as db:
        # 锁定并仅处理显式合成编号；不修改账号、商品、状态或用户新增业务记录。
        rows = db.scalars(
            select(Order)
            .where(or_(Order.order_no.like("SIM-%"), Order.order_no.like("DEMO-%")))
            .with_for_update()
        ).all()
        for row in rows:
            values = build_details(row.order_no, row.status, row.product)
            if any(getattr(row, key) is not None for key in values):
                skipped += 1  # 已补齐或存在人工编辑时整单跳过，避免覆盖。
                continue
            changed += 1
            if apply:
                for key, value in values.items():
                    setattr(row, key, value)
        return {"applied": apply, "enriched": changed, "skipped": skipped}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    print(enrich(apply=parser.parse_args().apply))
