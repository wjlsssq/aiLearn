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
  prompt_version: string // 本次请求使用的后端模板版本。
} // 本次问答结果。
export type ChatStreamEvent =
  | { event: 'start'; data: Pick<ChatResponse, 'mode' | 'model' | 'prompt_version'> }
  | { event: 'delta'; data: { text: string } }
  | { event: 'done'; data: ChatResponse } // 业务层只处理经过解析的流事件。
export interface HealthResponse {
  status: string
  database: string
  chat_mode: string
  model_name: string | null // 后端当前模型标识。
  model_configured: boolean // 必需字段是否齐全，不代表已验证密钥有效。
} // 服务状态。

export type PromptStyle = 'concise' | 'detailed' // 仅允许后端支持的回答风格。
export interface PromptOptions {
  store_name: string // 必填店铺名称，只作为业务标签。
  style: PromptStyle // 系统风格指令由后端映射。
}
export interface PromptPreview {
  template_id: string // 当前业务模板标识。
  version: string // 由后端维护的模板版本。
  messages: { role: 'system' | 'user'; content: string }[] // 完整消息，以文本呈现。
}
