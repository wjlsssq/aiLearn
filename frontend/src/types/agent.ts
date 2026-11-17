import type { AfterSalesDraft } from './draft'

export interface ChatArtifact {
  kind: 'orders' | 'draft'
  title: string
  columns: string[]
  rows: (string | number | null)[][]
  truncated: boolean
  draft: AfterSalesDraft | null
  missing_fields: string[]
}
