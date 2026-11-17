import type { ChatArtifact } from './agent'
// 与后端响应 DTO 对应的共享类型。
export interface LoginResponse {
  token: string
  username: string
} // 登录成功结果。
export interface Order {
  order_no: string
  product: string
  status: string
  quantity: number | null
  unit_price: string | null
  discount_amount: string | null
  shipping_fee: string | null
  total_amount: string | null
  paid_amount: string | null
  refund_amount: string | null
  created_at: string | null
  paid_at: string | null
  shipped_at: string | null
  delivered_at: string | null
  recipient_name: string | null
  recipient_phone: string | null
  province: string | null
  city: string | null
  district: string | null
  address: string | null
  shipping_company: string | null
  tracking_no: string | null
} // 当前用户订单。
export interface ChatSession {
  id: number
  title: string
} // 会话摘要。
export interface Message {
  role: string
  content: string
  artifacts: ChatArtifact[]
} // 单条历史消息。
export interface ChatResponse {
  session_id: number
  reply: string
  mode: string
  model: string | null // 实际使用的配置模型名，模拟模式为空。
  prompt_version: string // 本次请求使用的后端模板版本。
  artifacts: ChatArtifact[]
} // 本次问答结果。
export type ChatStreamEvent =
  | { event: 'start'; data: Pick<ChatResponse, 'mode' | 'model' | 'prompt_version'> }
  | { event: 'delta'; data: { text: string } }
  | { event: 'answer_reset'; data: Record<string, never> }
  | { event: 'activity'; data: { label: string } }
  | { event: 'artifact'; data: ChatArtifact }
  | { event: 'done'; data: ChatResponse } // 业务层只处理经过解析的流事件。
export interface HealthResponse {
  status: string
  database: string
  chat_mode: string
  model_name: string | null // 后端当前模型标识。
  model_configured: boolean // 必需字段是否齐全，不代表已验证密钥有效。
} // 服务状态。

export interface CurrentUser {
  username: string
}
