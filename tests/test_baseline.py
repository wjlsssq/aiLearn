"""使用教学 MySQL 的集成检查；只清理本测试创建的会话和令牌。"""
import hashlib  # 定位本次登录产生的令牌摘要。
from fastapi.testclient import TestClient  # 在本机执行 HTTP 请求。
from sqlalchemy import delete  # 使用参数化语句清理测试数据。
from backend.app.main import app  # 待验证的真实后端应用。
from backend.app.database import SessionLocal  # 清理独立事务。
from backend.app.models import AccessToken, ChatSession, ChatMessage  # 只操作测试产生的数据。

def test_database_auth_chat_and_isolation():  # 覆盖正常路径、持久化与越权失败路径。
    tokens = []  # 保存本次颁发的令牌，便于最后删除。
    session_id = None  # 只清理本次创建的会话。
    try:  # 即使断言失败，也执行清理。
        with TestClient(app) as client:  # 使用实际数据库依赖。
            assert client.get('/api/health').status_code == 200  # 数据库连接真实可用。
            assert client.get('/api/orders').status_code == 401  # 匿名用户不能查询订单。
            assert client.post('/api/login', json={'username':'alice','password':'wrong'}).status_code == 401  # 错误密码被拒绝。
            for name in ('alice','bob'):  # 为两个教学用户分别登录。
                response = client.post('/api/login', json={'username':name,'password':'Learn123!'})  # 使用种子账号。
                assert response.status_code == 200  # 认证应成功。
                tokens.append(response.json()['token'])  # 留存原始令牌用于本次请求。
            alice = {'Authorization':f'Bearer {tokens[0]}'}  # Alice 身份头。
            bob = {'Authorization':f'Bearer {tokens[1]}'}  # Bob 身份头。
            assert client.get('/api/orders', headers=alice).json()[0]['order_no'] == 'DEMO-A001'  # Alice 只看自己的订单。
            assert client.get('/api/orders', headers=bob).json()[0]['order_no'] == 'DEMO-B001'  # Bob 看到另一组数据。
            response = client.post('/api/chat', headers=alice, json={'message':'integration-check'})  # 创建测试会话。
            assert response.status_code == 200  # 问答入库成功。
            session_id = response.json()['session_id']  # 记录待清理主键。
            assert response.json()['mode'] == 'mock'  # 响应明确为模拟模式。
            assert client.get(f'/api/sessions/{session_id}/messages', headers=bob).status_code == 404  # Bob 不能读取 Alice 历史。
            assert client.post('/api/chat', headers=bob, json={'message':'forbidden','session_id':session_id}).status_code == 404  # Bob 不能写入 Alice 会话。
            assert client.post('/api/chat', headers=alice, json={'message':'   '}).status_code == 422  # 空白消息被拒绝。
        with TestClient(app) as fresh_client:  # 新的客户端仍应能读取已提交的数据。
            history = fresh_client.get(f'/api/sessions/{session_id}/messages', headers=alice).json()  # 从 MySQL 恢复历史。
            assert [row['role'] for row in history] == ['user','assistant']  # 被拒绝的跨用户消息没有写入。
    finally:  # 避免验证脚本污染学习数据。
        with SessionLocal.begin() as db:  # 清理动作在单独事务提交。
            if session_id is not None:  # 只清理测试实际创建的会话。
                db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))  # 先删除外键子记录。
                db.execute(delete(ChatSession).where(ChatSession.id == session_id))  # 再删除会话。
            for token in tokens:  # 不触碰用户其他登录记录。
                db.execute(delete(AccessToken).where(AccessToken.token_hash == hashlib.sha256(token.encode()).hexdigest()))  # 精确删除本次令牌。
