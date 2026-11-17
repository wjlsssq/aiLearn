"""有界订单导出、Excel 安全文本和认证下载业务。"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from time import time
from uuid import uuid4

import xlsxwriter

from ..core.errors import BusinessError
from ..models.order_export import OrderExport
from ..repositories import agent as audit
from ..repositories import order_export as repository
from ..schemas.agent import ChatArtifact

MAX_EXPORT_ROWS = 5000
MAX_FILE_BYTES = 4 * 1024 * 1024
EXPORT_TTL = 24 * 3600
MAX_ACTIVE_EXPORTS = 10
COLUMNS = {
    "order_no": "订单编号",
    "product": "商品",
    "status": "订单状态",
    "quantity": "数量",
    "unit_price": "单价（元）",
    "discount_amount": "优惠（元）",
    "shipping_fee": "运费（元）",
    "total_amount": "应付（元）",
    "paid_amount": "实付（元）",
    "refund_amount": "退款（元）",
    "created_at": "下单时间",
    "paid_at": "付款时间",
    "shipped_at": "发货时间",
    "delivered_at": "签收时间",
    "recipient_name": "收货人",
    "recipient_phone": "联系电话",
    "province": "省份",
    "city": "城市",
    "district": "区县",
    "address": "详细地址",
    "shipping_company": "物流公司",
    "tracking_no": "运单编号",
}


def build_workbook(rows, filters, now):
    output = BytesIO()
    with xlsxwriter.Workbook(
        output,
        {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False},
    ) as book:
        sheet = book.add_worksheet("订单明细")
        header = book.add_format(
            {"bold": True, "bg_color": "#EAF0FF", "font_color": "#264780", "bottom": 1}
        )
        money = book.add_format({"num_format": "#,##0.00"})
        date_format = book.add_format({"num_format": "yyyy-mm-dd hh:mm:ss"})
        sheet.write_row(0, 0, list(COLUMNS.values()), header)
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, len(rows), len(COLUMNS) - 1)
        sheet.set_column(0, len(COLUMNS) - 1, 18)
        sheet.set_column(1, 1, 30)
        sheet.set_column(19, 19, 55)
        sheet.set_column(10, 13, 22)
        for index, row in enumerate(rows, 1):
            for col, value in enumerate(row):
                if value is None:
                    continue  # 空白保留未知值，不能冒充金额 0。
                if isinstance(value, datetime):
                    sheet.write_datetime(index, col, value, date_format)
                elif isinstance(value, Decimal):
                    sheet.write_number(index, col, float(value), money)
                elif isinstance(value, int):
                    sheet.write_number(index, col, value)
                else:
                    sheet.write_string(
                        index, col, str(value)
                    )  # =、+、@ 等前缀始终作为文本，防止公式注入。
        info = book.add_worksheet("导出说明")
        info.set_column(0, 0, 20)
        info.set_column(1, 1, 75)
        metadata = [
            ("数据范围", "仅当前登录账号有权访问的订单；本文件为生成时快照"),
            ("时间口径", COLUMNS[filters.date_field]),
            (
                "日期范围",
                f"{filters.start_date} 至 {filters.end_date}（包含首尾两天，北京时间）",
            ),
            ("状态", filters.status or "全部"),
            ("商品包含", filters.product or "不限"),
            ("订单数量", len(rows)),
            (
                "生成时间",
                datetime.fromtimestamp(now, timezone(timedelta(hours=8))).isoformat(),
            ),
            ("金额说明", "人民币元；实付未扣退款；未知值留空"),
        ]
        for index, (key, value) in enumerate(metadata):
            info.write_string(index, 0, key)
            info.write_string(index, 1, str(value))
    return output.getvalue()


def create_export(user_id, request_id, filters):
    audit_id = audit.begin_audit(
        user_id, request_id, "EXPORT " + filters.model_dump_json()
    )
    state, code, count = "failed", "export_failed", 0
    started = time()
    try:
        rows = repository.read_rows(user_id, filters, COLUMNS, MAX_EXPORT_ROWS)
        if len(rows) > MAX_EXPORT_ROWS:
            raise BusinessError(
                422, "符合条件的订单超过 5000 笔，请缩小日期或筛选范围；未生成截断文件"
            )
        now = int(time())
        payload = build_workbook(rows, filters, now)
        if len(payload) > MAX_FILE_BYTES:
            raise BusinessError(422, "导出文件超过 4MB，请缩小筛选范围")
        identifier = str(uuid4())
        filename = f"订单_{filters.start_date}_{filters.end_date}.xlsx"
        record = OrderExport(
            id=identifier,
            user_id=user_id,
            filename=filename,
            row_count=len(rows),
            created_at=now,
            expires_at=now + EXPORT_TTL,
            payload=payload,
        )
        if not repository.save_snapshot(record, now, MAX_ACTIVE_EXPORTS):
            raise BusinessError(429, "当前有效导出已达 10 个，请待旧文件过期后再试")
        state, code, count = "succeeded", None, len(rows)
        return ChatArtifact(
            kind="export",
            title="订单 Excel 导出",
            export_id=identifier,
            filename=filename,
            row_count=len(rows),
            expires_at=now + EXPORT_TTL,
        )
    finally:
        audit.finish_audit(audit_id, state, int((time() - started) * 1000), count, code)


def download_export(db, user_id, export_id):
    record = repository.find_download(db, user_id, str(export_id), int(time()))
    if record is None:
        raise BusinessError(404, "导出文件不存在、尚未完成或已过期，请在聊天中重新导出")
    return record.filename, record.payload
