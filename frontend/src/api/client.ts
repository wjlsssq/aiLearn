import { readToken } from '../utils/auth-storage' // HTTP 层读取凭据，不依赖 Vue 页面。
import { createEventParser } from '../utils/sse' // 独立解析跨网络块的 SSE 帧。

export class ApiError extends Error {
  // 保留状态码，页面可以区分认证失败与网络故障。
  constructor(
    public readonly status: number,
    message: string,
  ) {
    // 显式定义错误契约。
    super(message) // 使用标准 Error 消息。
    this.name = 'ApiError' // 便于开发时定位错误来源。
  }
}
async function fetchResponse(path: string, body?: object, signal?: AbortSignal) {
  // JSON 与流式请求共享认证、HTTP 错误和本机代理路径。
  const token = readToken() // 每次读取最新凭据，避免旧闭包导致身份错乱。
  const headers: Record<string, string> = { 'Content-Type': 'application/json' } // JSON 请求的公共头。
  if (token) headers.Authorization = `Bearer ${token}` // 匿名请求不发送空的 Bearer 令牌。
  const response = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET',
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal, // 停止生成通过 AbortController 取消 HTTP 流。
  }) // 开发代理与生产反向代理共用 /api。
  if (!response.ok) {
    const data = await response.json().catch(() => ({})) // 错误页可能不是 JSON，不直接回显正文。
    // 非成功状态统一抛错，UI 由调用层处理。
    throw new ApiError(
      response.status,
      typeof data.detail === 'string' ? data.detail : '请求参数不正确',
    ) // 保持错误提示简洁。
  }
  return response
}

export async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetchResponse(path, body)
  return (await response.json()) as T // JSON 请求保持原有行为。
}

export async function requestStream(
  path: string,
  body: object,
  signal: AbortSignal,
  onEvent: (event: string, data: string) => void,
): Promise<void> {
  const response = await fetchResponse(path, body, signal)
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
    throw new ApiError(502, '后端未返回流式响应，请重启后端后再试')
  }
  const reader = response.body.getReader() // 逐块读取，不能使用 response.json/text 等待全文。
  const decoder = new TextDecoder() // 保留跨网络块的 UTF-8 中文字节。
  const parse = createEventParser(onEvent)
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      parse(decoder.decode(value, { stream: true }))
    }
    parse(decoder.decode()) // 刷新解码器；未结束的 SSE 帧不会冒充完整事件。
  } finally {
    await reader.cancel().catch(() => undefined) // 错误或主动中断也释放响应流。
    reader.releaseLock()
  }
}
