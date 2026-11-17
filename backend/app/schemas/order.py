"""订单查询响应，只暴露页面所需字段。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict  # 声明 HTTP 数据契约。


class OrderResponse(BaseModel):  # 当前用户订单项。
    model_config = ConfigDict(from_attributes=True)

    order_no: str  # 模拟订单号。
    product: str  # 商品名称。
    status: str  # 订单业务状态。
    quantity: int | None = None  # 数量。
    unit_price: Decimal | None = None  # 商品单价（元）。
    discount_amount: Decimal | None = None  # 优惠金额（元）。
    shipping_fee: Decimal | None = None  # 运费（元）。
    total_amount: Decimal | None = None  # 应付金额（元）。
    paid_amount: Decimal | None = None  # 实付金额（元）。
    refund_amount: Decimal | None = None  # 已退款金额（元）。
    created_at: datetime | None = None  # 下单时间。
    paid_at: datetime | None = None  # 付款时间。
    shipped_at: datetime | None = None  # 发货时间。
    delivered_at: datetime | None = None  # 签收时间。
    recipient_name: str | None = None  # 合成收货人。
    recipient_phone: str | None = None  # 合成联系电话。
    province: str | None = None  # 收货省份。
    city: str | None = None  # 收货城市。
    district: str | None = None  # 收货区县。
    address: str | None = None  # 收货详细地址。
    shipping_company: str | None = None  # 物流公司。
    tracking_no: str | None = None  # 合成物流单号。
