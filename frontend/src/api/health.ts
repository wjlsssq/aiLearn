import { request } from './client' // 公共 HTTP 处理。
import type { HealthResponse } from '../types/api' // 健康状态契约。
export const checkHealth = () => request<HealthResponse>('/health') // 真实数据库只读探针。
