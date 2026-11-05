import { request } from './client' // 统一 HTTP 入口。
import type { LoginResponse } from '../types/api' // 登录响应契约。
export const login = (username: string, password: string) =>
  request<LoginResponse>('/login', { username, password }) // 登录接口不操作页面状态。
