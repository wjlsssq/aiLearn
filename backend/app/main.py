"""阶段 0：真实数据库与认证，聊天响应明确使用模拟服务。"""
import hashlib  # 计算密码与令牌摘要。
import secrets  # 生成随机盐和不可预测的登录令牌。
import time  # 判断登录是否过期。
from fastapi import FastAPI, Depends, HTTPException  # 路由、依赖注入与明确 HTTP 状态。
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # 解析 Authorization 请求头。
from pydantic import BaseModel, Field  # 校验请求 DTO。
from sqlalchemy import select, text  # 使用参数化 ORM 查询。
from sqlalchemy.orm import Session  # 标注数据库会话类型。
from .database import get_db  # 注入请求级数据库连接。
from .models import User, AccessToken, Order, ChatSession, ChatMessage  # 使用持久化实体。

app = FastAPI(title="ShopMind 学习项目", version="0.1.0")  # /docs 提供可交互接口文档。
bearer = HTTPBearer(auto_error=False)  # 未登录统一返回 401。

def hash_password(password: str, salt: str) -> str:  # scrypt 增加离线猜测密码的成本。
    return salt + ":" + hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()  # 盐与摘要一起保存。

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:  # 用户身份由后端认证建立。
    if credentials is None:  # 拦截缺少凭据的请求。
        raise HTTPException(401, "请先登录")  # 前端据此显示登录界面。
    token = db.get(AccessToken, hashlib.sha256(credentials.credentials.encode()).hexdigest())  # 仅查询令牌摘要。
    if token is None or token.expires_at < int(time.time()):  # 校验令牌及有效期。
        raise HTTPException(401, "登录已失效，请重新登录")  # 不把失效登录继续传给业务层。
    user = db.get(User, token.user_id)  # 从数据库取得真实身份。
    if user is None:  # 已删除用户不能继续使用旧令牌。
        raise HTTPException(401, "用户不存在")  # 明确认证失败。
    return user  # 后续接口使用这个用户，而非请求中的 user_id。

class LoginInput(BaseModel):  # 登录 DTO。
    username: str = Field(min_length=1, max_length=64)  # 限制输入大小。
    password: str = Field(min_length=1, max_length=128)  # 密码只用于当前认证。

class ChatInput(BaseModel):  # 模拟聊天 DTO。
    message: str = Field(min_length=1, max_length=2000)  # 防止无限大的消息入库。
    session_id: int | None = None  # 不传表示建立新会话。

@app.get("/api/health")  # 用于前端检查后端与 MySQL。
def health(db: Session = Depends(get_db)):  # 实际执行数据库查询。
    try:  # 把连接问题转成可识别的服务状态。
        db.execute(text("SELECT 1"))  # 只读探针，不改变数据库。
    except Exception:  # 不向前端泄露连接密码等内部错误。
        raise HTTPException(503, "MySQL 暂不可用，请检查服务和环境配置") from None  # 返回明确服务不可用状态。
    return {"status": "ok", "database": "MySQL", "chat_mode": "mock"}  # 不伪装为真实模型调用。

@app.post("/api/login")  # 基础登录入口。
def login(body: LoginInput, db: Session = Depends(get_db)):  # 校验账号后颁发有期限的令牌。
    user = db.scalar(select(User).where(User.username == body.username))  # 用户名参数由 ORM 绑定。
    if user is None or not secrets.compare_digest(user.password_hash, hash_password(body.password, user.password_hash.split(":")[0])):  # 常量时间比较摘要。
        raise HTTPException(401, "账号或密码错误")  # 不区分账号不存在和密码错误。
    token = secrets.token_urlsafe(32)  # 原始令牌只返回一次给前端。
    db.add(AccessToken(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires_at=int(time.time()) + 86400))  # 有效期一天。
    db.commit()  # 令牌提交成功后才返回。
    return {"token": token, "username": user.username}  # 当前版本采用 Bearer 认证。

@app.get("/api/orders")  # 当前用户订单列表。
def orders(user: User = Depends(current_user), db: Session = Depends(get_db)):  # 登录是查询前提。
    rows = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id)).all()  # 在 SQL 层过滤用户归属。
    return [{"order_no": row.order_no, "product": row.product, "status": row.status} for row in rows]  # 只输出需要展示的字段。

@app.get("/api/sessions")  # 当前用户会话列表。
def sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):  # 不接收任意 user_id。
    return [{"id": row.id, "title": row.title} for row in db.scalars(select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.id.desc()))]  # 最近会话排在前面。

def owned_session(session_id: int, user: User, db: Session) -> ChatSession:  # 复用会话所有权校验。
    session = db.scalar(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))  # 同时筛选 ID 与归属。
    if session is None:  # 隐藏其他用户会话是否存在。
        raise HTTPException(404, "会话不存在")  # 越权请求无法读取历史。
    return session  # 已授权的会话实体。

@app.get("/api/sessions/{session_id}/messages")  # 恢复指定会话的历史。
def messages(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):  # 认证和连接由依赖注入。
    owned_session(session_id, user, db)  # 必须先检查所有权。
    return [{"role": row.role, "content": row.content} for row in db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id))]  # 按写入顺序返回。

@app.post("/api/chat")  # 阶段 0 的模拟聊天闭环。
def chat(body: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db)):  # 后续课程在此抽出真实模型服务。
    content = body.message.strip()  # 去掉无意义的首尾空格。
    if not content:  # 防止纯空白消息。
        raise HTTPException(422, "消息不能为空")  # 业务校验补充 DTO 长度校验。
    if body.session_id is None:  # 第一次提问新建会话。
        session = ChatSession(user_id=user.id, title=content[:40])  # 标题限制在字段长度内。
        db.add(session)  # 暂存会话实体。
        db.flush()  # 获取数据库生成的会话 ID，仍处于当前事务内。
    else:  # 已有会话必须校验归属。
        session = owned_session(body.session_id, user, db)  # 拒绝跨用户写入。
    reply = f"【模拟回复】已收到：{content}。当前用于验证前后端与 MySQL 链路；真实模型、规则检索和订单工具将在后续课程接入。"  # 不产生虚构业务承诺。
    db.add_all([ChatMessage(session_id=session.id, role="user", content=content), ChatMessage(session_id=session.id, role="assistant", content=reply)])  # 问答在同一事务写入。
    db.commit()  # 全部写入成功才返回，异常时依赖关闭会话并回滚。
    return {"session_id": session.id, "reply": reply, "mode": "mock"}  # 前端显式显示模拟模式。
