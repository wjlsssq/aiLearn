import { request } from './client' // 复用认证与统一 HTTP 错误处理。
import type { DraftReport } from '../types/draft'

export const extractDraft = (description: string) =>
  request<DraftReport>('/drafts/extract', { description })
