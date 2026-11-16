import { ref, watch, onBeforeUnmount, type Ref } from 'vue'
import { ApiError } from '../api/client'
import { queryOrder } from '../api/order'
import type { OrderAssistantResponse } from '../types/api'

export function useOrderAssistant(token: Ref<string>, logout: () => void) {
  const visible = ref(false),
    busy = ref(false),
    question = ref(''),
    error = ref('')
  const result = ref<OrderAssistantResponse | null>(null)
  let generation = 0
  watch(question, () => {
    result.value = null
    error.value = ''
  })
  watch(token, () => {
    generation++
    visible.value = false
    busy.value = false
    question.value = ''
    result.value = null
    error.value = ''
  })
  onBeforeUnmount(() => {
    generation++
  })
  function open(number?: string) {
    question.value = number ? `请查询订单 ${number} 的当前状态。` : ''
    result.value = null
    error.value = ''
    visible.value = true
  }
  async function run() {
    if (busy.value || !question.value.trim() || !token.value) return
    const current = generation
    busy.value = true
    result.value = null
    error.value = ''
    try {
      const response = await queryOrder(question.value.trim())
      if (current === generation) result.value = response
    } catch (caught) {
      if (current !== generation) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '订单查询失败，请稍后重试'
    } finally {
      if (current === generation) busy.value = false
    }
  }
  return { visible, busy, question, result, error, open, run }
}
