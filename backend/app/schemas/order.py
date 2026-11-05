"""订单查询响应，只暴露页面所需字段。"""

from pydantic import BaseModel  # 声明 HTTP 数据契约。


class OrderResponse(BaseModel):  # 当前用户订单项。
    order_no: str  # 模拟订单号。
    product: str  # 商品名称。
    status: str  # 订单业务状态。
