import type { AfterSalesDraft } from './draft'

export interface ChatArtifact {
  kind: 'orders' | 'draft' | 'export'
  title: string
  columns: string[]
  rows: (string | number | null)[][]
  truncated: boolean
  draft: AfterSalesDraft | null
  export_id?: string | null
  filename?: string | null
  row_count?: number | null
  expires_at?: number | null
  missing_fields: string[]
}
