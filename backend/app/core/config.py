"""读取项目根目录配置，工作目录变化不影响 .env 定位。"""

from pathlib import Path  # 定位仓库根目录。
from typing import Literal  # 将运行模式与供应商限制为明确选项。
from pydantic import Field, SecretStr  # 校验数值范围并隐藏凭据的默认展示。
from pydantic_settings import BaseSettings, SettingsConfigDict  # 校验配置类型。

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # core → app → backend → 仓库。


class Settings(BaseSettings):  # 配置对象在启动时执行类型校验。
    db_host: str = "127.0.0.1"  # 本机 MySQL 地址。
    db_port: int = 3306  # MySQL 端口。
    db_user: str = "root"  # 教学环境连接账号。
    db_password: str = ""  # 实际密码从 .env 加载。
    db_name: str = "langchain_lab"  # 独立教学数据库。
    chat_mode: Literal["mock", "llm"] = (
        "mock"  # 显式选择模拟或真实模型，失败时不自动切换。
    )
    llm_provider: Literal["openai_compatible", "deepseek"] = (
        "openai_compatible"  # 工厂选择适配器。
    )
    llm_base_url: str = ""  # 在 .env 填写所选服务的 API 基础地址。
    llm_model: str = ""  # 模型名称由所选服务定义，避免在业务代码中硬编码。
    llm_api_key: SecretStr = SecretStr("")  # 密钥仅在后端使用，不进入响应或普通 repr。
    llm_timeout_seconds: float = Field(default=30, gt=0, le=120)  # 单次网络请求超时。
    llm_temperature: float = Field(
        default=0.2, ge=0, le=2
    )  # 控制生成的随机性，不等于正确率。
    llm_max_tokens: int = Field(default=512, ge=1, le=4096)  # 限制本课输出预算。
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", extra="ignore"
    )  # 从项目根目录读取配置。


settings = Settings()  # 环境变量优先于 .env。
