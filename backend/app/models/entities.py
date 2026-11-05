"""阶段 0 的最小持久化实体；后续按课程逐步扩展。"""

from sqlalchemy import ForeignKey, String, Text  # 字段类型与数据库约束。
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
    )  # 当前阶段简化商品明细。
    status: Mapped[str] = mapped_column(
        String(32), comment="模拟订单状态"
    )  # 页面展示业务状态。


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
