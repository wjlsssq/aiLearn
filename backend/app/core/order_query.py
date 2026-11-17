"""将受支持的订单 SELECT 编译为带强制身份范围的参数化查询。"""

import re
from dataclasses import dataclass
from decimal import Decimal

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

VISIBLE_COLUMNS = {
    "city",
    "delivered_at",
    "quantity",
    "tracking_no",
    "shipping_fee",
    "total_amount",
    "shipping_company",
    "paid_at",
    "address",
    "recipient_name",
    "paid_amount",
    "created_at",
    "discount_amount",
    "product",
    "status",
    "district",
    "province",
    "order_no",
    "refund_amount",
    "shipped_at",
    "recipient_phone",
    "unit_price",
}
MAX_ROWS = 50
ALLOWED_NODES = {
    exp.Select,
    exp.From,
    exp.Table,
    exp.TableAlias,
    exp.Identifier,
    exp.Column,
    exp.Alias,
    exp.Star,
    exp.Literal,
    exp.Null,
    exp.Boolean,
    exp.Where,
    exp.Group,
    exp.Having,
    exp.Order,
    exp.Ordered,
    exp.Limit,
    exp.Offset,
    exp.Distinct,
    exp.And,
    exp.Or,
    exp.Not,
    exp.Paren,
    exp.EQ,
    exp.NEQ,
    exp.GT,
    exp.GTE,
    exp.LT,
    exp.LTE,
    exp.Like,
    exp.In,
    exp.Between,
    exp.Is,
    exp.Count,
    exp.Sum,
    exp.Avg,
    exp.Min,
    exp.Max,
    exp.Lower,
    exp.Upper,
}


@dataclass(frozen=True)
class CompiledOrderQuery:
    sql: str
    parameters: dict
    limit: int


def compile_order_query(sql: str, user_id: int) -> CompiledOrderQuery:
    if not 1 <= len(sql) <= 2000 or type(user_id) is not int or user_id <= 0:
        raise ValueError("查询长度或身份无效")
    try:
        statements = sqlglot.parse(sql, read="mysql")
    except (ParseError, TokenError, RecursionError):
        raise ValueError("SQL 语法无效，请按 my_orders 表结构重新生成") from None
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("只允许一条 SELECT 查询")
    query = statements[0]
    nodes = list(query.walk())
    if len(nodes) > 150 or any(
        type(node) not in ALLOWED_NODES or node.comments for node in nodes
    ):
        raise ValueError(
            "只支持单表筛选、排序、分组、COUNT/SUM/AVG/MIN/MAX；不支持注释、子查询、联表或其他函数"
        )
    tables = list(query.find_all(exp.Table))
    if (
        len(tables) != 1
        or tables[0].name.lower() != "my_orders"
        or tables[0].db
        or tables[0].catalog
    ):
        raise ValueError("只能查询逻辑表 my_orders，不允许访问其他表或数据库")
    if len(query.expressions) > 8:
        raise ValueError("最多返回八列")
    table = tables[0]
    source_alias = table.alias_or_name
    aliases = {item.alias.lower() for item in query.expressions if item.alias}
    for identifier in query.find_all(exp.Identifier):
        if not re.fullmatch(r"[\w\u4e00-\u9fff]{1,32}", identifier.name):
            raise ValueError("字段和别名只能包含字母、数字、中文或下划线")
    for column in query.find_all(exp.Column):
        if column.table and column.table.lower() != source_alias.lower():
            raise ValueError("字段必须来自当前订单逻辑表")
        is_output_alias = (
            column.name.lower() in aliases
            and column.find_ancestor(exp.Order, exp.Having, exp.Group) is not None
        )
        if (
            column.name.lower() not in VISIBLE_COLUMNS
            and not is_output_alias
            and not isinstance(column.this, exp.Star)
        ):
            raise ValueError("字段不在订单业务白名单中，请按工具说明选择")
    # SELECT * 展开为公开列；COUNT(*) 保留，仅针对强制用户范围统计。
    projections = []
    for index, item in enumerate(query.expressions):
        if (
            isinstance(item, exp.Star)
            or isinstance(item, exp.Column)
            and isinstance(item.this, exp.Star)
        ):
            projections.extend(
                exp.column(name, table=source_alias)
                for name in ("order_no", "product", "status")
            )
        else:
            projections.append(
                item
                if isinstance(item, (exp.Column, exp.Alias))
                else item.as_(
                    "订单数" if isinstance(item, exp.Count) else f"结果{index + 1}"
                )
            )
    query.set("expressions", projections)
    if len(projections) > 8:
        raise ValueError("最多返回八列")

    def bounded_integer(node, default, upper):
        if node is None:
            return default
        value = node.expression
        if (
            not isinstance(value, exp.Literal)
            or value.is_string
            or not value.this.isdigit()
        ):
            raise ValueError("LIMIT/OFFSET 必须为非负整数")
        return min(int(value.this), upper)

    limit = bounded_integer(query.args.get("limit"), MAX_ROWS, MAX_ROWS)
    if limit < 1:
        raise ValueError("LIMIT 至少为 1")
    offset = bounded_integer(query.args.get("offset"), 0, 2000)
    if query.args.get("offset") and int(query.args["offset"].expression.this) > 2000:
        raise ValueError("分页偏移最多为 2000")
    query.limit(limit + 1, copy=False)  # 多取一条仅用于说明结果是否被截断。
    if offset:
        query.offset(offset, copy=False)
    scoped = sqlglot.parse_one(
        "SELECT order_no, product, status, quantity, unit_price, discount_amount, shipping_fee, total_amount, paid_amount, refund_amount, created_at, paid_at, shipped_at, delivered_at, recipient_name, recipient_phone, province, city, district, address, shipping_company, tracking_no FROM agent_order_data WHERE user_id = 0",
        read="mysql",
    )
    scoped.args["where"].this.set("expression", exp.Placeholder(this="actor_id"))
    table.replace(
        scoped.subquery(alias=source_alias)
    )  # 用户 WHERE 在派生表之外，OR 1=1 也不能扩大归属。
    parameters = {"actor_id": user_id}
    for index, literal in enumerate(list(query.find_all(exp.Literal))):
        name = f"value_{index}"
        if literal.is_string:
            value = literal.this
        else:
            value = Decimal(literal.this)
            if not value.is_finite() or abs(value) > 10**9:
                raise ValueError("数值常量超出查询范围")
            value = int(value) if value == value.to_integral_value() else value
        parameters[name] = value
        literal.replace(
            exp.Placeholder(this=name)
        )  # 字符串与数字都绑定，用户文本不进入执行 SQL。
    compiled = query.sql(dialect="mysql", identify=True)
    return CompiledOrderQuery(compiled, parameters, limit)
