import type { Order } from './api'

export interface OrderToolResult {
  status: 'found' | 'not_found' | 'invalid_arguments' | 'unknown_tool' | 'error'
  message: string
  order: Order | null
  logistics: string | null
}
export interface ToolStep {
  stage: 'model' | 'tool'
  label: string
  status: 'done' | 'failed' | 'blocked'
  message: string
  call_id: string | null
  name: string | null
  arguments: Record<string, string>
  result: OrderToolResult | null
}
export interface ToolReport {
  mode: 'mock' | 'llm'
  status: 'complete' | 'blocked' | 'failed'
  answer: string | null
  model_calls: number
  tool_executions: number
  steps: ToolStep[]
}
export interface OrderToolDefinition {
  name: string
  description: string
  parameters: Record<string, unknown>
  max_tool_executions: number
  max_model_calls: number
}
