import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { runChain } from '../api/chain'
import { ApiError } from '../api/client'
import type { PromptOptions } from '../types/api'
import type { ChainMethod, ChainReport } from '../types/chain'

export function useChainLab(token: Ref<string>, logout: () => void) {
  const visible = ref(false)
  const busy = ref(false)
  const method = ref<ChainMethod>('invoke')
  const first = ref('  退货需要什么资料？\r\n')
  const second = ref('  收到商品破损怎么办？  ')
  const prompt = ref<PromptOptions>({ store_name: '', style: 'concise' })
  const report = ref<ChainReport | null>(null)
  const error = ref('')
  let version = 0 // 登出、关闭或编辑后不展示旧请求的结果。
  onBeforeUnmount(() => {
    version++
  })
  const valid = computed(() =>
    Boolean(
      prompt.value.store_name.trim() &&
      first.value.trim() &&
      (method.value === 'invoke' || second.value.trim()),
    ),
  )
  watch([method, first, second], () => {
    report.value = null
    error.value = ''
  })
  watch(token, () => {
    version++
    visible.value = false
    report.value = null
    busy.value = false
  })
  watch(visible, () => {
    version++
    report.value = null
    error.value = ''
  })

  function open(options: PromptOptions, draft: string) {
    prompt.value = { ...options } // 实验固定本次配置，不受聊天中的后续编辑影响。
    if (draft.trim()) first.value = draft
    visible.value = true
  }

  async function run(inspect: boolean) {
    if (busy.value || !valid.value) return
    const current = ++version
    busy.value = true
    error.value = ''
    report.value = null
    try {
      const result = await runChain(
        {
          questions: method.value === 'invoke' ? [first.value] : [first.value, second.value],
          method: method.value,
          prompt: { ...prompt.value },
        },
        inspect,
      )
      if (current === version) report.value = result
    } catch (caught) {
      if (current !== version) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '实验请求失败'
    } finally {
      if (current === version) busy.value = false
    }
  }
  return { visible, busy, method, first, second, prompt, report, error, valid, open, run }
}
