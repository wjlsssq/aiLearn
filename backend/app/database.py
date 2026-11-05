"""数据库配置：类似 Spring 的数据源配置。"""
from pydantic_settings import BaseSettings, SettingsConfigDict  # 加载本机环境变量。
from sqlalchemy import URL, create_engine  # 安全拼装连接信息，避免密码中的特殊字符破坏 URL。
from sqlalchemy.orm import DeclarativeBase, sessionmaker  # 提供实体基类和会话工厂。

class Settings(BaseSettings):  # 配置对象在启动时执行类型校验。
    db_host: str = "127.0.0.1"  # 本机 MySQL 地址。
    db_port: int = 3306  # MySQL 端口。
    db_user: str = "root"  # 教学环境连接账号。
    db_password: str = ""  # 实际密码从 .env 加载。
    db_name: str = "langchain_lab"  # 独立教学数据库。
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # 从项目根目录读取配置。

settings = Settings()  # 构建应用配置，环境变量优先于文件。
url = URL.create("mysql+pymysql", username=settings.db_user, password=settings.db_password, host=settings.db_host, port=settings.db_port, database=settings.db_name, query={"charset": "utf8mb4"})  # 参数化构造数据源。
engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800, connect_args={"connect_timeout": 5})  # 检查失效连接并设置超时。
SessionLocal = sessionmaker(bind=engine)  # 每个请求创建独立事务会话。

class Base(DeclarativeBase):  # 所有实体共享此元数据入口。
    pass  # 字段由子类定义。

def get_db():  # FastAPI 依赖，相当于按请求注入数据库会话。
    with SessionLocal() as db:  # 请求结束自动关闭连接并回滚未提交事务。
        yield db  # 将会话交给当前接口使用。
