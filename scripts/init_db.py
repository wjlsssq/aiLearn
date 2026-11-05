"""显式初始化教学数据库；不会删除已有表或清空数据。"""

import secrets  # 为教学密码生成随机盐。
from backend.app.core.config import settings  # 初始化与应用共用配置。
from sqlalchemy import create_engine, select, text  # 初始化与参数化查询。
from backend.app.db.session import url, Base, engine, SessionLocal  # 共享数据源定义。
from backend.app.models import User, Order  # 导入模型以注册元数据。
from backend.app.core.security import hash_password  # 种子账号与登录使用同一密码算法。

if settings.db_name != "langchain_lab":  # 初始化脚本只操作约定教学库。
    raise RuntimeError(
        "Initialization only supports langchain_lab."
    )  # 防止配置错误操作其他库。
server = create_engine(
    url._replace(database=None)
)  # 清除数据库字段，建库前只连接服务端。
try:  # 无论成功失败都释放临时连接池。
    with server.begin() as connection:  # 显式事务管理。
        connection.execute(
            text("CREATE DATABASE IF NOT EXISTS langchain_lab CHARACTER SET utf8mb4")
        )  # 幂等创建独立教学库。
finally:  # 不保留初始化连接。
    server.dispose()  # 关闭服务端连接池。
Base.metadata.create_all(engine)  # 阶段 0 基线；后续表结构变更使用 Alembic 迁移。
with SessionLocal.begin() as db:  # 种子用户和订单一起提交。
    for name, product, number in [
        ("alice", "无线降噪耳机", "DEMO-A001"),
        ("bob", "便携蓝牙音箱", "DEMO-B001"),
    ]:  # 两个用户用于隔离验证。
        user = db.scalar(
            select(User).where(User.username == name)
        )  # 重复运行不会覆盖已有密码。
        if user is None:  # 只补充缺失的教学账号。
            user = User(
                username=name,
                password_hash=hash_password("Learn123!", secrets.token_hex(16)),
            )  # 合成账号的公开教学密码。
            db.add(user)  # 注册账号。
            db.flush()  # 获取用户主键。
        if (
            db.scalar(select(Order).where(Order.order_no == number)) is None
        ):  # 订单种子同样幂等。
            db.add(
                Order(
                    order_no=number,
                    user_id=user.id,
                    product=product,
                    status="已签收（模拟）",
                )
            )  # 写入该用户的独立订单。
print(
    "Database ready. Demo users: alice / bob; password: Learn123!"
)  # 不打印 MySQL 凭据。
