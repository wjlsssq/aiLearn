"""Q07 起用 Alembic 增量迁移；阶段 0 的五张表由 init_db 建立基线。"""

from alembic import context
from backend.app.db.session import engine, Base
from backend.app import models  # 注册实体，但不导入 FastAPI 应用。


if context.is_offline_mode():
    context.configure(url=engine.url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
