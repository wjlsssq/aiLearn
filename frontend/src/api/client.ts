import { readToken } from '../utils/auth-storage' // HTTP 层读取凭据，不依赖 Vue 页面。

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
export async function request<T>(path: string, body?: object): Promise<T> {
  // 通用请求的响应类型由业务 API 声明。
  const token = readToken() // 每次读取最新凭据，避免旧闭包导致身份错乱。
  const headers: Record<string, string> = { 'Content-Type': 'application/json' } // JSON 请求的公共头。
  if (token) headers.Authorization = `Bearer ${token}` // 匿名请求不发送空的 Bearer 令牌。
  const response = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  }) // 开发代理与生产反向代理共用 /api。
  const data = await response.json() // 读取服务端响应。
  if (!response.ok) {
    // 非成功状态统一抛错，UI 由调用层处理。
    throw new ApiError(
      response.status,
      typeof data.detail === 'string' ? data.detail : '请求参数不正确',
    ) // 保持错误提示简洁。
  }
  return data as T // 后端 response_model 保证响应 DTO；调用处获得明确类型。
}
