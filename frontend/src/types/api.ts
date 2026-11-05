// 与后端响应 DTO 对应的共享类型。
export interface LoginResponse {
  token: string
  username: string
} // 登录成功结果。
export interface Order {
  order_no: string
  product: string
  status: string
} // 当前用户订单。
export interface ChatSession {
  id: number
  title: string
} // 会话摘要。
export interface Message {
  role: string
  content: string
} // 单条历史消息。
export interface ChatResponse {
  session_id: number
  reply: string
  mode: string
  model: string | null // 实际使用的配置模型名，模拟模式为空。
} // 本次问答结果。
export interface HealthResponse {
  status: string
  database: string
  chat_mode: string
  model_name: string | null // 后端当前模型标识。
  model_configured: boolean // 必需字段是否齐全，不代表已验证密钥有效。
} // 服务状态。
