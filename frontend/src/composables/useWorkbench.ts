import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue' // 响应式状态与请求生命周期。
import { ElMessage } from 'element-plus' // 展示业务操作失败提示。
import { ApiError } from '../api/client' // 根据状态码恢复登录页面。
import { currentUser as getCurrentUser, login as loginRequest } from '../api/auth' // 登录请求。
import { logout as signOut } from '../api/auth'
import { listOrders } from '../api/order' // 订单请求。
import { listSessions, listMessages, streamMessage } from '../api/chat' // 会话与增量聊天请求。
import { checkHealth } from '../api/health' // 系统探针请求。
import { readToken, saveToken, clearToken } from '../utils/auth-storage' // 统一凭据存储。
import type { Order, ChatSession } from '../types/api' // 页面共享类型。
import type { ChatMessage, ChatTurn } from '../types/chat' // 仅用于当前页面的发送状态。

export function useWorkbench() {
  // 一次调用对应一个工作台实例，不创建全局用户状态。
  const username = ref('') // 不在产品中预填或公开演示账号。
  const password = ref('') // 凭据只在本次登录提交。
  const token = ref(readToken()) // 恢复当前标签页的登录状态。
  const status = ref('正在检查') // 系统健康状态。
  const modelConfigured = ref(false) // 真实模式缺少配置时提示用户补齐。
  const busy = ref(false) // 串行化用户操作，避免会话切换竞争。
  const sending = ref(false) // 模型生成不再占用整个页面的 busy 状态。
  const input = ref('') // 当前输入内容。
  const history = ref<ChatMessage[]>([]) // 立即展示的消息与持久化历史。
  const sessions = ref<ChatSession[]>([]) // 当前用户会话列表。
  const orders = ref<Order[]>([]) // 当前用户订单。
  const sessionId = ref<number | null>(null) // null 表示新会话。
  const currentUser = ref('') // 身份从受认证接口恢复。
  const retryableTurn = ref<ChatTurn | null>(null) // 只重试当前会话的最后一个未完成问答。
  const retryMessageId = computed(() => retryableTurn.value?.assistant.localId ?? null)
  let controller: AbortController | null = null // 当前模型请求的取消入口。
  let activeTask: Promise<void> | null = null // 切换会话前等待当前流退出。
  let conversationVersion = 0 // 退出或切换后拒绝旧请求回写页面。
  function resetConversation() {
    // 新会话操作只更新页面状态，发送时才建库记录。
    sessionId.value = null // 清空当前会话 ID。
    history.value = [] // 清空展示内容。
    retryableTurn.value = null // 未保存问答不能被带到其他会话重试。
    conversationVersion += 1 // 旧请求和会话列表刷新不再更新新页面。
  }
  async function stopAndWait() {
    if (!controller) return
    controller.abort() // 取消 fetch，使服务端关闭上游模型流。
    await activeTask // 清理结束后才允许替换当前会话。
  }
  function stop() {
    controller?.abort() // 单独停止生成，不清空已经显示的内容或新输入草稿。
  }
  async function newSession() {
    if (busy.value) return
    busy.value = true
    try {
      await stopAndWait()
      resetConversation()
    } finally {
      busy.value = false
    }
  }
  function clearIdentity() {
    // 退出后彻底清除当前用户展示数据。
    token.value = '' // 切换到登录界面。
    clearToken() // 删除标签页凭据。
    orders.value = [] // 防止残留上一位用户订单。
    sessions.value = [] // 清空会话摘要。
    input.value = '' // 不保留上一位用户未发送的文本。
    currentUser.value = ''
    username.value = ''
    password.value = ''
    controller?.abort()
    resetConversation() // 认证过期时同步清空，避免等待自己的发送任务造成死锁。
  }
  async function logout() {
    await stopAndWait()
    try {
      await signOut()
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401))
        ElMessage.warning('服务端退出未确认，已清除本机登录状态')
    }
    clearIdentity()
  }
  function reportError(error: unknown) {
    // 统一业务操作错误反馈。
    if (error instanceof ApiError && error.status === 401) clearIdentity() // 认证过期时清除页面状态。
    ElMessage.error(error instanceof Error ? error.message : '请求失败，请稍后重试') // 未知错误也提供安全提示。
  }
  async function refresh() {
    // 加载当前用户业务数据。
    const [identity, orderRows, sessionRows] = await Promise.all([
      getCurrentUser(),
      listOrders(),
      listSessions(),
    ])
    currentUser.value = identity.username
    orders.value = orderRows
    sessions.value = sessionRows
  }
  async function login() {
    // 表单提交后的认证流程。
    busy.value = true // 禁止重复操作。
    try {
      // 登录成功后加载业务数据。
      const data = await loginRequest(username.value, password.value) // 提交账号凭据。
      token.value = data.token // 更新页面登录状态。
      currentUser.value = data.username
      password.value = '' // 登录完成立即清除表单密码。
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
      await stopAndWait() // 用户切换会话时停止旧回复，不让流写进另一个会话。
      // 查询成功后再切换状态。
      const data = await listMessages(id) // 读取持久化历史。
      conversationVersion += 1
      retryableTurn.value = null
      sessionId.value = id // 更新选中的会话。
      history.value = data // 原子替换当前消息列表。
    } catch (error) {
      reportError(error) // 查询失败保留原会话。
    } finally {
      busy.value = false // 恢复交互。
    }
  }
  async function runTurn(turn: ChatTurn) {
    // 问题与配置在发起时固定，用户可以继续编辑下一条草稿。
    const requestController = new AbortController()
    const version = conversationVersion
    controller = requestController
    sending.value = true
    retryableTurn.value = null
    turn.user.status = 'pending'
    turn.assistant.status = 'pending'
    turn.assistant.content = ''
    turn.assistant.error = undefined
    let saved = false
    try {
      await streamMessage(turn.question, turn.sessionId, requestController.signal, (event) => {
        if (version !== conversationVersion) return // 旧会话或旧身份不能更新当前页面。
        if (event.event === 'delta') {
          turn.assistant.status = 'streaming'
          turn.assistant.content += event.data.text // 每收到一块就显示，不在前端模拟打字。
        } else if (event.event === 'done') {
          saved = true // done 表示模型结束且数据库提交成功。
          sessionId.value = event.data.session_id
          turn.assistant.content = event.data.reply // 与最终入库正文保持一致。
          turn.assistant.status = 'complete'
          turn.user.status = 'complete'
        }
      })
    } catch (error) {
      if (version === conversationVersion && !saved) {
        turn.user.status = 'error'
        turn.assistant.status = requestController.signal.aborted ? 'stopped' : 'error'
        turn.assistant.error = requestController.signal.aborted
          ? '已停止生成'
          : error instanceof Error
            ? error.message
            : '回复中断，请稍后重试'
        retryableTurn.value = turn // 保留原始问题和配置，重试不重复追加用户消息。
        if (error instanceof ApiError && error.status === 401) reportError(error)
      }
    } finally {
      if (controller === requestController) {
        controller = null
        sending.value = false
      }
    }
    if (saved && version === conversationVersion) {
      // 会话列表刷新失败不能把已保存的回复标为发送失败，也不能触发模型重试。
      void listSessions()
        .then((data) => {
          if (version === conversationVersion) sessions.value = data
        })
        .catch((error: unknown) => {
          if (version !== conversationVersion) return
          if (error instanceof ApiError && error.status === 401) reportError(error)
          else ElMessage.warning('回复已保存，会话列表刷新失败，请稍后刷新')
        })
    }
  }
  async function send() {
    const question = input.value.trim()
    if (!question || busy.value || sending.value || !modelConfigured.value) return
    const turn: ChatTurn = {
      question,
      sessionId: sessionId.value,
      user: reactive({
        localId: crypto.randomUUID(),
        role: 'user',
        content: question,
        status: 'pending',
      }),
      assistant: reactive({
        localId: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        status: 'pending',
      }),
    }
    history.value.push(turn.user, turn.assistant) // 发请求前先显示用户消息和助手占位。
    input.value = '' // 立即释放输入框，下一条草稿不会被请求结束时清除。
    activeTask = runTurn(turn)
    await activeTask
  }
  async function retry(id: string) {
    const turn = retryableTurn.value
    if (!turn || turn.assistant.localId !== id || sending.value || busy.value) return
    activeTask = runTurn(turn) // 使用相同气泡重新生成，不覆盖当前输入框草稿。
    await activeTask
  }
  onBeforeUnmount(() => controller?.abort()) // 页面卸载时不遗留后台读取任务。
  onMounted(async () => {
    // 页面挂载时恢复可用状态。
    try {
      // 健康探针成功后再加载业务数据。
      const health = await checkHealth() // 探测数据库及本地模型配置，不调用模型。
      modelConfigured.value = health.chat_mode === 'llm' && health.model_configured // 未配置时禁止提交真实调用。
      status.value = modelConfigured.value ? '服务已连接' : '智能服务尚未启用' // 区分数据库状态和配置状态。
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
    currentUser,
    password,
    token,
    status,
    modelConfigured,
    busy,
    sending,
    retryMessageId,
    input,
    history,
    sessions,
    orders,
    sessionId,
    newSession,
    login,
    logout,
    openSession,
    send,
    stop,
    retry,
  } // 页面只调用业务操作，不依赖请求细节。
}
