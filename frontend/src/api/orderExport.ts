import { requestBlob } from './client'

export function downloadOrderExport(id: string, signal: AbortSignal) {
  return requestBlob(`/order-exports/${encodeURIComponent(id)}/download`, signal)
}
