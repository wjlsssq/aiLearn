<script setup lang="ts">
import { ref, onMounted } from 'vue' // 使用响应式状态与页面初始化钩子。
import { ElMessage } from 'element-plus' // 统一显示请求失败信息。
type Message = { role: string; content: string } // 前后端约定的消息结构。
const username = ref('alice'), password = ref('Learn123!') // 预填公开的教学账号。
const token = ref(sessionStorage.getItem('shopmind-token') || '') // 仅在当前标签页保存登录状态。
const status = ref('正在检查'), busy = ref(false), input = ref('') // 页面状态与提交锁。
const history = ref<Message[]>([]), sessions = ref<{id:number; title:string}[]>([]) // 保存当前消息与会话列表。
const orders = ref<{order_no:string; product:string; status:string}[]>([]) // 当前登录用户的模拟订单。
const sessionId = ref<number | null>(null) // null 表示下一次提问创建会话。
async function api(path: string, body?: object) { // 集中封装请求头和错误处理。
  const response = await fetch('/api' + path, { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token.value}` }, body: body ? JSON.stringify(body) : undefined }) // 通过 Vite 代理访问后端。
  const data = await response.json() // 解析后端统一 JSON 响应。
  if (!response.ok) { // HTTP 失败不能当成正常业务结果。
    if (response.status === 401) logout() // 登录过期后清空本地凭据。
    throw new Error(typeof data.detail === 'string' ? data.detail : '请求参数不正确') // 不把校验数组直接显示给用户。
  }
  return data // 返回已验证状态码的数据。
}
function logout() { token.value = ''; sessionStorage.removeItem('shopmind-token'); history.value = []; orders.value = []; sessions.value = []; sessionId.value = null } // 清空当前用户页面数据。
async function refresh() { // 刷新登录用户的数据。
  orders.value = await api('/orders') // 订单归属由服务端过滤。
  sessions.value = await api('/sessions') // 获取当前用户的会话列表。
}
async function login() { // 登录过程显示加载状态，防止重复提交。
  busy.value = true // 锁定提交入口。
  try { const data = await api('/login', { username: username.value, password: password.value }); token.value = data.token; sessionStorage.setItem('shopmind-token', data.token); await refresh() } // 保存有效令牌后加载数据。
  catch (error) { ElMessage.error(String(error)) } // 显示认证或连接失败。
  finally { busy.value = false } // 所有分支都释放提交锁。
}
async function openSession(id: number) { // 切换会话时重新读取数据库历史。
  busy.value = true // 请求期间禁止继续发送或切换。
  try { const data = await api(`/sessions/${id}/messages`); sessionId.value = id; history.value = data } // 成功后同时切换 ID 与消息。
  catch (error) { ElMessage.error(String(error)) } // 保留原会话并报告错误。
  finally { busy.value = false } // 恢复交互。
}
async function send() { // 本阶段仅调用明确标识的模拟聊天接口。
  const message = input.value.trim() // 去掉空白文本。
  if (!message || busy.value) return // 避免空请求与重复提交。
  busy.value = true // 锁定当前会话。
  try { const data = await api('/chat', { message, session_id: sessionId.value }); sessionId.value = data.session_id; history.value.push({role:'user',content:message},{role:'assistant',content:data.reply}); input.value = ''; sessions.value = await api('/sessions') } // 数据库提交成功才更新消息。
  catch (error) { ElMessage.error(String(error)) } // 失败时保留输入，便于重试。
  finally { busy.value = false } // 完成后允许下一条消息。
}
onMounted(async () => { // 页面首次加载检查系统状态。
  try { await api('/health'); status.value = '服务正常 · MySQL 已连接'; if (token.value) await refresh() } // 恢复登录但不自动打开旧会话。
  catch (error) { status.value = '服务暂不可用'; ElMessage.error(String(error)) } // 明确显示连接失败。
})
</script>

<template>
  <!-- 页面按“会话、聊天、业务信息”组织，便于观察完整请求闭环。 -->
  <div class="workspace">
    <aside class="sidebar">
      <div class="brand">S<span>ShopMind</span></div><p class="muted">智能售后客服 · 学习工作台</p>
      <div class="stage">阶段 0 / 基础应用闭环</div>
      <el-button v-if="token" :disabled="busy" class="new-chat" @click="sessionId=null;history=[]">＋ 新建会话</el-button>
      <p class="section-label">会话记录</p>
      <button v-for="item in sessions" :key="item.id" class="session" :class="{active:sessionId===item.id}" :disabled="busy" @click="openSession(item.id)">{{ item.title }}</button>
      <div class="sidebar-bottom">Vue → FastAPI → MySQL<br>每一步，都能看见。</div>
    </aside>
    <main>
      <header><div><p class="eyebrow">CUSTOMER SUPPORT</p><h1>售后服务助手</h1></div><div class="status">● {{ status }} <el-button v-if="token" :disabled="busy" size="small" @click="logout">退出登录</el-button></div></header>
      <div v-if="!token" class="login-card">
        <p class="eyebrow">WELCOME TO SHOPMIND</p><h2>从一段对话开始</h2><p class="muted">登录教学账号，体验有身份隔离的聊天与订单查询。</p>
        <el-form @submit.prevent="login"><el-form-item label="账号"><el-input v-model="username" autocomplete="username" /></el-form-item><el-form-item label="密码"><el-input v-model="password" type="password" show-password autocomplete="current-password" /></el-form-item><el-button native-type="submit" type="primary" :loading="busy">进入工作台</el-button></el-form>
        <p class="muted">教学账号 alice / bob，密码均为 Learn123!</p>
      </div>
      <div v-else class="content">
        <section class="chat-panel">
          <div class="panel-top"><span>客服对话</span><el-tag type="warning" effect="plain">模拟响应</el-tag></div>
          <div class="messages" aria-live="polite">
            <div v-if="!history.length" class="welcome"><div class="spark">✦</div><h2>你好，有什么可以帮你？</h2><p>先试着提问，观察消息如何保存到 MySQL。</p><el-button @click="input='这款耳机可以退货吗？'">这款耳机可以退货吗？</el-button><p class="muted">本阶段尚未接入真实模型与知识库。</p></div>
            <article v-for="(message,index) in history" :key="index" class="message" :class="message.role"><span class="role">{{ message.role==='user'?'你':'ShopMind' }}</span><p>{{ message.content }}</p></article>
          </div>
          <form class="composer" @submit.prevent="send"><el-input v-model="input" aria-label="输入消息" placeholder="输入你的问题…" :maxlength="2000" :disabled="busy" /><el-button type="primary" native-type="submit" :loading="busy">发送</el-button></form>
        </section>
        <aside class="details"><div class="panel-top">我的订单 <el-tag effect="plain">教学数据</el-tag></div><div v-for="order in orders" :key="order.order_no" class="order"><small>{{ order.order_no }}</small><h3>{{ order.product }}</h3><p>{{ order.status }}</p></div><p class="muted">这里只展示当前登录用户的订单。切换 alice / bob 可观察数据隔离。</p><el-button :disabled="busy" @click="logout">退出登录</el-button></aside>
      </div>
    </main>
  </div>
</template>

<style>
/* 基础色彩与尺寸统一定义，保证工作台视觉一致。 */
:root{font-family:Inter,"Microsoft YaHei",sans-serif;color:#203a36;background:#f3f6f4;--el-color-primary:#267966}*{box-sizing:border-box}body{margin:0}button{font:inherit}h1,h2,h3,p{margin-top:0}.workspace{display:flex;min-height:100vh}.sidebar{width:245px;background:#173d35;color:#fff;padding:30px 22px;display:flex;flex-direction:column;flex-shrink:0}.brand{font-size:22px;font-weight:700;display:flex;gap:12px;align-items:center}.brand>span{font-size:23px}.sidebar .muted{color:#abc7bd;font-size:12px;margin-top:14px}.stage{font-size:12px;border:1px solid #51776b;padding:12px;border-radius:8px;margin:22px 0}.section-label{font-size:12px;color:#abc7bd;margin:30px 0 10px}.session{border:0;background:transparent;color:#cde2d9;text-align:left;padding:12px;border-radius:8px;cursor:pointer;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.session.active,.session:hover{background:#30584c}.sidebar-bottom{margin-top:auto;padding-top:50px;font-size:12px;line-height:2;color:#abc7bd}main{flex:1;min-width:0;padding:34px 40px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}h1{font-size:27px;margin-bottom:0}.eyebrow{font-size:10px;letter-spacing:2px;color:#66847a}.status{font-size:12px;color:#477b66}.muted{font-size:13px;color:#7b8e86;line-height:1.8}.content{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:24px}.chat-panel,.details,.login-card{background:#fff;border:1px solid #e2eae4;border-radius:16px}.chat-panel{display:flex;flex-direction:column;height:calc(100vh - 150px);min-height:450px}.panel-top{padding:20px;border-bottom:1px solid #edf1ed;font-weight:600;display:flex;justify-content:space-between;align-items:center;font-size:14px}.messages{flex:1;overflow:auto;padding:24px}.welcome{text-align:center;margin:70px auto;color:#526f63}.welcome h2{font-size:23px}.welcome>p{font-size:13px;margin-top:20px}.spark{font-size:44px;color:#38927a;margin-bottom:20px}.composer{display:flex;gap:12px;padding:20px;border-top:1px solid #edf1ed}.message{max-width:90%;margin-bottom:22px}.message.user{margin-left:auto;text-align:right}.role{font-size:11px;color:#81948a}.message p{padding:14px 18px;border-radius:12px;background:#f1f5f2;font-size:14px;line-height:1.9;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:8px}.message.user p{background:#e0f1e9;text-align:left}.details{align-self:start;padding-bottom:20px}.details>.muted,.details>.el-button{margin:20px}.order{padding:20px;border-bottom:1px solid #edf1ed}.order small{color:#87988e}.order h3{font-size:15px;margin:12px 0}.order p{font-size:12px;color:#348365;margin:0}.login-card{max-width:480px;margin:60px auto;padding:36px}.login-card h2{margin:20px 0}.login-card .el-form{margin-top:30px}@media(max-width:1050px){.content{grid-template-columns:1fr}.details{display:block}.sidebar{width:210px}main{padding:25px}}@media(max-width:650px){.sidebar{display:none}main{padding:18px}.status{max-width:130px}.chat-panel{height:calc(100vh - 130px)}.login-card{padding:24px;margin:20px auto}}
</style>
