"""订单业务输出，不向外暴露完整 ORM 实体。"""

from sqlalchemy.orm import Session  # 当前事务上下文。
from ..schemas.order import OrderResponse  # 类型明确的输出 DTO。
from ..repositories import order as repository  # 订单数据访问。


def list_orders(
    db: Session, user_id: int
) -> list[OrderResponse]:  # 输出当前用户订单的页面字段。
    return [
        OrderResponse(order_no=row.order_no, product=row.product, status=row.status)
        for row in repository.list_orders(db, user_id)
    ]  # 身份不能由模型或前端任意指定。
