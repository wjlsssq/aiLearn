"""无数据库和 HTTP 依赖的密码、令牌工具。"""

import hashlib  # 计算摘要。
import secrets  # 常量时间比较。


def hash_password(password: str, salt: str) -> str:  # scrypt 增加离线猜测密码的成本。
    return (
        salt
        + ":"
        + hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
        ).hex()
    )  # 盐与摘要一起保存。


def token_digest(token: str) -> str:  # 原始令牌不进入数据库。
    return hashlib.sha256(token.encode()).hexdigest()  # 返回固定长度摘要。


def verify_password(password: str, stored_hash: str) -> bool:  # 登录只比较密码摘要。
    try:  # 存量数据损坏时按认证失败处理。
        candidate = hash_password(
            password, stored_hash.split(":")[0]
        )  # 使用存储的盐计算。
        return secrets.compare_digest(stored_hash, candidate)  # 常量时间比较。
    except ValueError:  # 无效盐或无效编码不应成为 500。
        return False  # 保持认证失败语义。
