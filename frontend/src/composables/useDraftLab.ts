import { ref, watch, onBeforeUnmount, type Ref } from 'vue'
import { extractDraft } from '../api/draft'
import { ApiError } from '../api/client'
import type { DraftReport } from '../types/draft'

export function useDraftLab(token: Ref<string>, logout: () => void) {
  const visible = ref(false)
  const busy = ref(false)
  const description = ref('订单 DEMO-A001 的耳机左耳没有声音，我想换货，数量 1 件。')
  const report = ref<DraftReport | null>(null)
  const error = ref('')
  let version = 0 // 身份变更后拒收旧结果，避免跨账号展示。
  watch(description, () => {
    report.value = null
    error.value = ''
  })
  watch(token, () => {
    version++
    visible.value = false
    report.value = null
    description.value = '' // 不继承上一位用户的描述。
    error.value = ''
    busy.value = false
  })
  onBeforeUnmount(() => {
    version++
  })
  async function run() {
    if (busy.value || !description.value.trim() || !token.value) return
    const current = ++version
    busy.value = true
    error.value = ''
    report.value = null
    try {
      const result = await extractDraft(description.value.trim())
      if (current === version) report.value = result
    } catch (caught) {
      if (current !== version) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '草稿提取失败'
    } finally {
      if (current === version) busy.value = false
    }
  }
  return { visible, busy, description, report, error, run }
}
