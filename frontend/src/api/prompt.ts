import { request } from './client' // 复用认证和错误处理，不在组件内发 HTTP。
import type { PromptOptions, PromptPreview } from '../types/api' // 与后端 DTO 对齐。

export const previewPrompt = (message: string, options: PromptOptions) =>
  request<PromptPreview>('/prompts/preview', { message, ...options }) // 只预览，不调用模型。
