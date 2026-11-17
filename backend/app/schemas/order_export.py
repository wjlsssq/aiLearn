"""订单导出的业务筛选条件，不接受身份、SQL 或服务器文件路径。"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderExportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date
    date_field: Literal["created_at", "paid_at", "shipped_at", "delivered_at"] = (
        "created_at"
    )
    status: str | None = Field(default=None, min_length=1, max_length=32)
    product: str | None = Field(default=None, min_length=1, max_length=80)

    @model_validator(mode="after")
    def check_range(self):
        if not date(2000, 1, 1) <= self.start_date <= self.end_date < date(2100, 1, 1):
            raise ValueError("开始日期不得晚于结束日期，日期范围为 2000～2099 年")
        if (self.end_date - self.start_date).days > 365:
            raise ValueError("一次最多导出连续 366 天，请缩小日期范围")
        return self
