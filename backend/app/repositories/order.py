"""订单数据访问，SQL 层限定用户归属。"""

from sqlalchemy import select  # 参数化查询。
from sqlalchemy.orm import Session  # 数据库会话。
from ..models import Order  # 订单实体。


def list_orders(db: Session, user_id: int) -> list[Order]:  # 只查询当前用户的订单。
    return list(
        db.scalars(select(Order).where(Order.user_id == user_id).order_by(Order.id))
    )  # 明确返回顺序。
