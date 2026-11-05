import type { Message, PromptOptions } from './api' // UI 状态不混进后端消息 DTO。

export interface ChatMessage extends Message {
  localId?: string // 本次页面中稳定的消息标识。
  status?: 'pending' | 'streaming' | 'complete' | 'error' | 'stopped'
  error?: string // 安全错误文本，不放供应商原始响应。
}
export interface ChatTurn {
  question: string // 保留重试时的原始问题。
  prompt: PromptOptions // 请求发起时的配置快照，不读取后来编辑的值。
  sessionId: number | null
  user: ChatMessage
  assistant: ChatMessage
}
