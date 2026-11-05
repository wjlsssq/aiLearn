import { request } from './client' // 公共 HTTP 处理。
import type { ChatResponse, ChatSession, Message, PromptOptions } from '../types/api' // 聊天与会话契约。
export const listSessions = () => request<ChatSession[]>('/sessions') // 当前用户会话。
export const listMessages = (id: number) => request<Message[]>(`/sessions/${id}/messages`) // 服务端校验会话归属。
export const sendMessage = (message: string, sessionId: number | null, prompt: PromptOptions) =>
  request<ChatResponse>('/chat', { message, session_id: sessionId, prompt }) // 配置随本次请求发送。
