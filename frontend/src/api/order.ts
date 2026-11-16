import { request } from './client' // 公共 HTTP 处理。
import type { Order, OrderAssistantResponse } from '../types/api' // 订单 DTO。
export const listOrders = () => request<Order[]>('/orders') // 用户身份由服务端认证确定。

export const queryOrder = (question: string) =>
  request<OrderAssistantResponse>('/assistant/orders', { question })
