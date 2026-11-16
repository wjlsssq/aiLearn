// Q06：结构化提取报告，不把草稿等同于已确认工单。
export interface AfterSalesDraft {
  order_no: string | null
  issue_type: 'return' | 'exchange' | 'refund' | 'other' | 'unknown'
  reason: string | null
  quantity: number | null
}
export interface DraftReport {
  mode: 'mock' | 'llm'
  schema_version: string
  valid: boolean
  draft: AfterSalesDraft | null
  issues: string[]
  missing_fields: string[]
}
