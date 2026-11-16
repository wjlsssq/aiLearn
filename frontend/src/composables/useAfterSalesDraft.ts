import { ref, watch, onBeforeUnmount, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { extractDraft } from '../api/draft'
import { ApiError } from '../api/client'
import type { DraftReport } from '../types/draft'

export function useAfterSalesDraft(token: Ref<string>, logout: () => void) {
  const visible = ref(false),
    busy = ref(false),
    description = ref(''),
    error = ref('')
  const report = ref<DraftReport | null>(null)
  let generation = 0
  watch(description, () => {
    report.value = null
    error.value = ''
  })
  watch(token, () => {
    generation++
    visible.value = false
    busy.value = false
    description.value = ''
    report.value = null
    error.value = ''
  })
  onBeforeUnmount(() => {
    generation++
  })
  function open(value = '') {
    description.value = value
    report.value = null
    error.value = ''
    visible.value = true
  }
  async function run() {
    if (busy.value || !description.value.trim() || !token.value) return
    const current = generation
    busy.value = true
    report.value = null
    error.value = ''
    try {
      const result = await extractDraft(description.value.trim())
      if (current === generation) report.value = result
    } catch (caught) {
      if (current !== generation) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '信息整理失败，请稍后重试'
    } finally {
      if (current === generation) busy.value = false
    }
  }
  async function copy() {
    const draft = report.value?.draft
    if (!draft) return
    try {
      await navigator.clipboard.writeText(
        `订单编号：${draft.order_no ?? '待补充'}\n问题类型：${{ return: '退货', exchange: '换货', refund: '退款', other: '其他', unknown: '待确认' }[draft.issue_type]}\n原因：${draft.reason ?? '待补充'}\n数量：${draft.quantity ?? '待补充'}`,
      )
      ElMessage.success('资料已复制')
    } catch {
      ElMessage.error('复制失败，请手动选择文字复制')
    }
  }
  return { visible, busy, description, error, report, open, run, copy }
}
