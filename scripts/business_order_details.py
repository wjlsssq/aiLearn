"""可复现的合成订单明细；不使用真实个人信息。"""

import hashlib
import random
from datetime import datetime, timedelta
from decimal import Decimal


def build_details(order_no: str, status: str, product: str = "") -> dict:
    # 每个编号独立种子，重跑或更换批次不会改变已有订单的明细。
    rng = random.Random(hashlib.sha256(order_no.encode()).hexdigest())
    quantity = rng.randint(1, 4)
    # 根据商品类别设置价格区间，避免出现显示器只卖几十元的失真样本。
    prices = [
        ("显示器", 129900),
        ("投影", 199900),
        ("阅读器", 89900),
        ("手表", 69900),
        ("耳机", 39900),
        ("键盘", 29900),
        ("数据线", 3990),
        ("HDMI", 4990),
        ("净化器", 159900),
        ("摄像头", 29900),
        ("手环", 19900),
        ("鼠标", 9900),
    ]
    base = next((value for name, value in prices if name in product), 15900)
    price = (Decimal(base) / 100 * Decimal(rng.choice(["1", "1.2", "1.5"]))).quantize(
        Decimal("0.01")
    )
    goods = price * quantity
    discount = (goods * Decimal(rng.choice(["0", "0.05", "0.10"]))).quantize(
        Decimal("0.01")
    )
    shipping = Decimal("0.00") if goods >= 199 else Decimal("8.00")
    total = goods - discount + shipping
    created = datetime(2026, 11, 8, 0, 0) - timedelta(
        minutes=rng.randint(0, 180 * 1440)
    )
    unpaid = status in {"待付款", "已取消"}
    paid = None if unpaid else created + timedelta(minutes=rng.randint(1, 90))
    shipped = (
        None
        if unpaid or status == "待发货"
        else paid + timedelta(hours=rng.randint(2, 24))
    )
    delivered = (
        shipped + timedelta(days=rng.randint(1, 4))
        if status in {"已签收", "已签收（模拟）", "已完成", "售后中", "已退款"}
        else None
    )
    province, city, district = rng.choice(
        [
            ("浙江省", "杭州市", "西湖区"),
            ("广东省", "深圳市", "南山区"),
            ("四川省", "成都市", "武侯区"),
            ("江苏省", "南京市", "鼓楼区"),
            ("湖北省", "武汉市", "洪山区"),
            ("陕西省", "西安市", "雁塔区"),
        ]
    )
    return {
        "quantity": quantity,
        "unit_price": price,
        "discount_amount": discount,
        "shipping_fee": shipping,
        "total_amount": total,
        "paid_amount": Decimal("0.00") if unpaid else total,
        "refund_amount": total if status == "已退款" else Decimal("0.00"),
        "created_at": created,
        "paid_at": paid,
        "shipped_at": shipped,
        "delivered_at": delivered,
        "recipient_name": f"测试收件人{rng.randint(1, 999):03d}",
        # 000 前缀不是可投递手机号，地址和运单也明确使用测试标识。
        "recipient_phone": f"000{rng.randrange(100000000):08d}",
        "province": province,
        "city": city,
        "district": district,
        "address": f"模拟路{rng.randint(1, 999)}号测试园区{rng.randint(1, 20)}栋（合成地址，勿投递）",
        "shipping_company": rng.choice(["顺丰速运", "中通快递", "圆通速递"])
        if shipped
        else None,
        "tracking_no": f"TEST-{order_no}" if shipped else None,
    }
