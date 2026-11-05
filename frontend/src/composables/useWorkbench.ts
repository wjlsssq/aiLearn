import { ref, computed, watch, onMounted } from 'vue' // 响应式状态、派生校验与生命周期。
import { ElMessage } from 'element-plus' // 展示业务操作失败提示。
import { ApiError } from '../api/client' // 根据状态码恢复登录页面。
import { login as loginRequest } from '../api/auth' // 登录请求。
import { listOrders } from '../api/order' // 订单请求。
import { listSessions, listMessages, sendMessage } from '../api/chat' // 会话与聊天请求。
import { checkHealth } from '../api/health' // 系统探针请求。
import { previewPrompt as previewPromptRequest } from '../api/prompt' // 模板预览请求。
import { readToken, saveToken, clearToken } from '../utils/auth-storage' // 统一凭据存储。
import type { Message, Order, ChatSession, PromptStyle, PromptPreview } from '../types/api' // 页面共享类型。

export function useWorkbench() {
  // 一次调用对应一个工作台实例，不创建全局用户状态。
  const username = ref('alice') // 公开教学用户名。
  const password = ref('Learn123!') // 教学密码，非数据库连接密码。
  const token = ref(readToken()) // 恢复当前标签页的登录状态。
  const status = ref('正在检查') // 系统健康状态。
  const chatMode = ref('mock') // 以服务端健康接口返回的模式为准。
  const modelName = ref<string | null>(null) // 页面只展示模型名，不接触 API Key。
  const modelConfigured = ref(true) // 真实模式缺少配置时提示用户补齐。
  const busy = ref(false) // 串行化用户操作，避免会话切换竞争。
  const previewBusy = ref(false) // 区分预览加载与模型发送加载。
  const input = ref('') // 当前输入内容。
  const history = ref<Message[]>([]) // 当前会话消息。
  const sessions = ref<ChatSession[]>([]) // 当前用户会话列表。
  const orders = ref<Order[]>([]) // 当前用户订单。
  const sessionId = ref<number | null>(null) // null 表示新会话。
  const storeName = ref('ShopMind 教学店') // Q02：仅保存在当前工作台的业务变量。
  const promptStyle = ref<PromptStyle>('concise') // 默认使用简洁风格。
  const promptPreview = ref<PromptPreview | null>(null) // 后端渲染的消息，不在前端复制模板。
  const previewVisible = ref(false) // 控制预览弹窗，展示与请求状态分开。
  const lastPromptVersion = ref<string | null>(null) // 最近一次成功问答的模板版本。
  const promptValid = computed(() => Boolean(storeName.value.trim())) // 避免发送空白店铺名。
  watch([input, storeName, promptStyle], () => {
    promptPreview.value = null // 输入或配置变化后清除旧预览，避免把旧消息当成当前消息。
    previewVisible.value = false // 已失效的预览不继续展示。
  })
  function newSession() {
    // 新会话操作只更新页面状态，发送时才建库记录。
    sessionId.value = null // 清空当前会话 ID。
    history.value = [] // 清空展示内容。
  }
  function logout() {
    // 退出后彻底清除当前用户展示数据。
    token.value = '' // 切换到登录界面。
    clearToken() // 删除标签页凭据。
    orders.value = [] // 防止残留上一位用户订单。
    sessions.value = [] // 清空会话摘要。
    input.value = '' // 不保留上一位用户未发送的文本。
    storeName.value = 'ShopMind 教学店' // 新登录用户从默认业务配置开始。
    promptStyle.value = 'concise' // 不继承上一位用户的风格选择。
    promptPreview.value = null // 清除上一位用户的问题预览。
    previewVisible.value = false // 关闭可能仍在显示的弹窗。
    lastPromptVersion.value = null // 清除上一位用户的请求信息。
    newSession() // 重置消息和会话 ID。
  }
  function reportError(error: unknown) {
    // 统一业务操作错误反馈。
    if (error instanceof ApiError && error.status === 401) logout() // 认证过期时清除页面状态。
    ElMessage.error(error instanceof Error ? error.message : '请求失败，请稍后重试') // 未知错误也提供安全提示。
  }
  async function refresh() {
    // 加载当前用户业务数据。
    orders.value = await listOrders() // 订单范围在后端控制。
    sessions.value = await listSessions() // 恢复会话摘要。
  }
  async function login() {
    // 表单提交后的认证流程。
    busy.value = true // 禁止重复操作。
    try {
      // 登录成功后加载业务数据。
      const data = await loginRequest(username.value, password.value) // 提交账号凭据。
      token.value = data.token // 更新页面登录状态。
      saveToken(data.token) // 后续 HTTP 请求读取最新凭据。
      await refresh() // 加载订单与会话。
    } catch (error) {
      reportError(error) // 处理认证和网络错误。
    } finally {
      busy.value = false // 所有分支均释放交互锁。
    }
  }
  async function openSession(id: number) {
    // 用户选择历史会话。
    if (busy.value) return // 避免并发切换导致历史覆盖。
    busy.value = true // 锁定输入和切换操作。
    try {
      // 查询成功后再切换状态。
      const data = await listMessages(id) // 读取持久化历史。
      sessionId.value = id // 更新选中的会话。
      history.value = data // 原子替换当前消息列表。
    } catch (error) {
      reportError(error) // 查询失败保留原会话。
    } finally {
      busy.value = false // 恢复交互。
    }
  }
  function currentPromptOptions() {
    // 预览和发送从同一份状态读取参数，后端负责最终校验。
    return { store_name: storeName.value.trim(), style: promptStyle.value }
  }
  async function previewPrompt() {
    // 预览不需要模型密钥；与发送共用 busy，期间禁止编辑或切换会话。
    if (busy.value || !input.value.trim() || !promptValid.value) return
    busy.value = true // 防止重复请求和配置变化。
    previewBusy.value = true // 加载反馈显示在实际触发的预览按钮上。
    try {
      promptPreview.value = await previewPromptRequest(input.value.trim(), currentPromptOptions())
      previewVisible.value = true // 成功取得消息后再打开弹窗。
    } catch (error) {
      reportError(error) // 错误仍走统一反馈和认证过期处理。
    } finally {
      previewBusy.value = false // 结束预览专属的加载反馈。
      busy.value = false // 无论成功失败都恢复编辑。
    }
  }
  async function send() {
    // 模拟问答也采用真实的持久化接口。
    const message = input.value.trim() // 去除首尾空白。
    if (!message || busy.value || !promptValid.value) return // 校验问题与必填业务变量。
    busy.value = true // 当前请求期间不切换会话。
    try {
      // 服务端提交成功后再更新页面。
      const data = await sendMessage(message, sessionId.value, currentPromptOptions()) // 附带当前 Prompt 配置。
      chatMode.value = data.mode // 成功响应再次确认实际模式。
      modelName.value = data.model // 展示本次使用的模型。
      lastPromptVersion.value = data.prompt_version // 使用服务端返回的版本，避免前端猜测。
      sessionId.value = data.session_id // 保存服务端生成的 ID。
      history.value.push(
        { role: 'user', content: message },
        { role: 'assistant', content: data.reply },
      ) // 展示成功问答。
      input.value = '' // 成功后清空输入。
      sessions.value = await listSessions() // 更新新建的会话标题。
    } catch (error) {
      reportError(error) // 失败时保留输入便于重试。
    } finally {
      busy.value = false // 恢复提交入口。
    }
  }
  onMounted(async () => {
    // 页面挂载时恢复可用状态。
    try {
      // 健康探针成功后再加载业务数据。
      const health = await checkHealth() // 探测数据库及本地模型配置，不调用模型。
      chatMode.value = health.chat_mode // 不在前端自行决定模型调用方式。
      modelName.value = health.model_name // 展示配置中的模型名。
      modelConfigured.value = health.model_configured // 未配置时禁止提交真实调用。
      status.value = health.model_configured
        ? '服务正常 · MySQL 已连接'
        : 'MySQL 已连接 · 模型待配置' // 区分数据库状态和配置状态。
    } catch (error) {
      status.value = '服务暂不可用'
      reportError(error)
      return // 健康探测失败时不继续请求业务数据。
    } // 展示连接失败原因。
    if (token.value) {
      // 登录过期仅影响身份，不把数据库状态误标为故障。
      try {
        await refresh()
      } catch (error) {
        reportError(error)
      } // 恢复当前账号数据。
    }
  })
  return {
    username,
    password,
    token,
    status,
    chatMode,
    modelName,
    modelConfigured,
    busy,
    previewBusy,
    input,
    history,
    sessions,
    orders,
    sessionId,
    storeName,
    promptStyle,
    promptPreview,
    previewVisible,
    lastPromptVersion,
    promptValid,
    newSession,
    login,
    logout,
    openSession,
    send,
    previewPrompt,
  } // 页面只调用业务操作，不依赖请求细节。
}
