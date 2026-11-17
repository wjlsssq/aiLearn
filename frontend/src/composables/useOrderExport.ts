import { onBeforeUnmount, ref } from 'vue'
import { downloadOrderExport } from '../api/orderExport'
import { readToken } from '../utils/auth-storage'

export function useOrderExport() {
  const downloading = ref(false)
  const error = ref('')
  let controller: AbortController | null = null
  onBeforeUnmount(() => controller?.abort()) // 切换会话后停止旧组件的下载。

  async function download(id: string, filename: string) {
    if (downloading.value) return
    const token = readToken()
    const task = new AbortController()
    controller = task
    downloading.value = true
    error.value = ''
    try {
      const blob = await downloadOrderExport(id, task.signal)
      if (task.signal.aborted || token !== readToken()) return // 身份变化后不交付旧账号文件。
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.append(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (cause) {
      if (!task.signal.aborted)
        error.value = cause instanceof Error ? cause.message : '下载失败，请重试'
    } finally {
      downloading.value = false
      controller = null
    }
  }
  return { downloading, error, download }
}
