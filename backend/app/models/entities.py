"""账号、订单与会话持久化实体。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)  # 字段类型与数据库约束。
from sqlalchemy.orm import Mapped, mapped_column  # 声明带类型的 ORM 字段。

from ..db.session import Base  # 共享实体基类。


class User(Base):  # 教学用户，避免把用户身份交给模型决定。
    __tablename__ = "users"  # 映射的表名。
    id: Mapped[int] = mapped_column(
        primary_key=True, comment="用户主键"
    )  # 内部用户标识。
    username: Mapped[str] = mapped_column(
        String(64), unique=True, comment="唯一登录名"
    )  # 唯一约束避免重复账号。
    password_hash: Mapped[str] = mapped_column(
        String(256), comment="加盐密码摘要"
    )  # 不保存明文密码。


class AccessToken(Base):  # 登录状态持久化，后端重启不会清空有效登录。
    __tablename__ = "access_tokens"  # 独立认证令牌表。
    token_hash: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="令牌 SHA256 摘要"
    )  # 不保存原始令牌。
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, comment="归属用户"
    )  # 登录身份来自服务端。
    expires_at: Mapped[int] = mapped_column(
        comment="到期 Unix 时间戳"
    )  # 过期后必须重新登录。


class Order(Base):  # 所有订单均为合成教学数据。
    __tablename__ = "orders"  # 模拟订单表。
    id: Mapped[int] = mapped_column(primary_key=True, comment="订单主键")  # ORM 主键。
    order_no: Mapped[str] = mapped_column(
        String(32), unique=True, comment="订单编号"
    )  # 对外展示编号。
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, comment="订单归属用户"
    )  # 查询必须附带此条件。
    product: Mapped[str] = mapped_column(
        String(128), comment="模拟商品名称"
    )  # 一单一商品规格；金额与收货信息为下单快照。
    status: Mapped[str] = mapped_column(
        String(32), comment="模拟订单状态"
    )  # 页面展示业务状态。

    # 新字段允许为空，旧业务记录不伪造默认金额或时间；样本由脚本明确补齐。
    quantity: Mapped[int | None] = mapped_column(
        Integer(), nullable=True, comment="数量"
    )
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="商品单价（元）"
    )
    discount_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="优惠金额（元）"
    )
    shipping_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="运费（元）"
    )
    total_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="应付金额（元）"
    )
    paid_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="实付金额（元）"
    )
    refund_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="已退款金额（元）"
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True, comment="下单时间"
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True, comment="付款时间"
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True, comment="发货时间"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True, comment="签收时间"
    )
    recipient_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="合成收货人"
    )
    recipient_phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="合成联系电话"
    )
    province: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="收货省份"
    )
    city: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="收货城市"
    )
    district: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="收货区县"
    )
    address: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="收货详细地址"
    )
    shipping_company: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="物流公司"
    )
    tracking_no: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="合成物流单号"
    )


class ChatSession(Base):  # 会话列表按用户隔离。
    __tablename__ = "chat_sessions"  # 会话元信息表。
    id: Mapped[int] = mapped_column(
        primary_key=True, comment="会话主键"
    )  # 前端选择会话使用此值。
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, comment="会话归属用户"
    )  # 服务端校验所有权。
    title: Mapped[str] = mapped_column(
        String(80), default="新会话", comment="会话标题"
    )  # 首条消息生成标题。


class ChatMessage(Base):  # 数据库存的是历史，不代表模型已获得记忆。
    __tablename__ = "chat_messages"  # 消息表。
    id: Mapped[int] = mapped_column(
        primary_key=True, comment="消息主键及排序依据"
    )  # 按主键恢复消息顺序。
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id"), index=True, comment="所属会话"
    )  # 外键约束。
    role: Mapped[str] = mapped_column(
        String(16), comment="user 或 assistant"
    )  # 对话角色。
    content: Mapped[str] = mapped_column(Text, comment="消息正文")  # 保存文本。
    artifacts: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="已完成回复的业务结果"
    )
