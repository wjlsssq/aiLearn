"""查询审计不暴露给智能体；记录每次尝试及执行边界。"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import Base


class AgentQueryAudit(Base):
    __tablename__ = "agent_query_audits"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    query_text: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(16))
    row_count: Mapped[int] = mapped_column(default=0)
    elapsed_ms: Mapped[int] = mapped_column(default=0)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[int] = mapped_column()
