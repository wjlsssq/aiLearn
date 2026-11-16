import { request } from './client'
import type { ToolReport, OrderToolDefinition } from '../types/tool-calling'

export const getOrderToolSchema = () => request<OrderToolDefinition>('/tool-calling/schema')
export const runOrderTool = (question: string) =>
  request<ToolReport>('/tool-calling/run', { question })
