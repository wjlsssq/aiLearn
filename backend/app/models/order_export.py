"""订单 Excel 快照；下载有效期独立于聊天历史保留时间。"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import Base


class OrderExport(Base):
    __tablename__ = "order_exports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(128))
    row_count: Mapped[int]
    created_at: Mapped[int]
    expires_at: Mapped[int] = mapped_column(index=True)
    payload: Mapped[bytes] = mapped_column(MEDIUMBLOB)
