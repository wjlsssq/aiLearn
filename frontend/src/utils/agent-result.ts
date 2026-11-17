import type { ChatArtifact } from '../types/agent'

export function isChatArtifact(value: unknown): value is ChatArtifact {
  if (!value || typeof value !== 'object') return false
  const item = value as Record<string, unknown>
  return (
    ['orders', 'draft'].includes(String(item.kind)) &&
    typeof item.title === 'string' &&
    Array.isArray(item.columns) &&
    item.columns.every((column) => typeof column === 'string') &&
    Array.isArray(item.rows) &&
    item.rows.every(
      (row) =>
        Array.isArray(row) &&
        row.every((cell) => cell === null || typeof cell === 'string' || typeof cell === 'number'),
    ) &&
    typeof item.truncated === 'boolean' &&
    Array.isArray(item.missing_fields) &&
    item.missing_fields.every((field) => typeof field === 'string') &&
    (item.kind === 'orders' || isDraft(item.draft))
  )
}

function isDraft(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false
  const draft = value as Record<string, unknown>
  return (
    (draft.order_no === null || typeof draft.order_no === 'string') &&
    ['return', 'exchange', 'refund', 'other', 'unknown'].includes(String(draft.issue_type)) &&
    (draft.reason === null || typeof draft.reason === 'string') &&
    (draft.quantity === null ||
      (typeof draft.quantity === 'number' &&
        Number.isInteger(draft.quantity) &&
        draft.quantity >= 1 &&
        draft.quantity <= 99))
  )
}
