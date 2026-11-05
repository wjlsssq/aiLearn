import { ApiError, request, requestStream } from './client' // 公共 HTTP 与流式处理。
import type {
  ChatResponse,
  ChatSession,
  ChatStreamEvent,
  Message,
  PromptOptions,
} from '../types/api'
export const listSessions = () => request<ChatSession[]>('/sessions') // 当前用户会话。
export const listMessages = (id: number) => request<Message[]>(`/sessions/${id}/messages`) // 服务端校验会话归属。
export const sendMessage = (message: string, sessionId: number | null, prompt: PromptOptions) =>
  request<ChatResponse>('/chat', { message, session_id: sessionId, prompt }) // 配置随本次请求发送。

export async function streamMessage(
  message: string,
  sessionId: number | null,
  prompt: PromptOptions,
  signal: AbortSignal,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<ChatResponse> {
  let result: ChatResponse | undefined // 只有 done 能确认问答已完整保存。
  await requestStream(
    '/chat/stream',
    { message, session_id: sessionId, prompt },
    signal,
    (event, raw) => {
      let data
      try {
        data = JSON.parse(raw)
      } catch {
        throw new ApiError(502, '流式消息格式错误，请重新打开会话核对')
      }
      if (!data || typeof data !== 'object' || Array.isArray(data)) {
        throw new ApiError(502, '流式消息格式错误，请重新打开会话核对')
      }
      if (event === 'error') {
        throw new ApiError(
          typeof data.status === 'number' ? data.status : 502,
          typeof data.message === 'string' ? data.message : '回复生成失败',
        )
      }
      if (
        event === 'start' &&
        typeof data.mode === 'string' &&
        typeof data.prompt_version === 'string'
      ) {
        onEvent({ event, data })
      } else if (event === 'delta' && typeof data.text === 'string') {
        onEvent({ event, data })
      } else if (
        event === 'done' &&
        typeof data.session_id === 'number' &&
        typeof data.reply === 'string' &&
        typeof data.mode === 'string' &&
        typeof data.prompt_version === 'string'
      ) {
        result = data
        onEvent({ event, data })
      } else if (['start', 'delta', 'done'].includes(event)) {
        throw new ApiError(502, '流式消息缺少必要字段，请重新打开会话核对')
      }
    },
  )
  if (!result) throw new ApiError(502, '连接已中断，保存状态未确认，请重新打开会话核对后重试')
  return result
}
