import { ref, watch, onBeforeUnmount, type Ref } from 'vue'
import { ApiError } from '../api/client'
import { getOrderToolSchema, runOrderTool } from '../api/tool-calling'
import type { ToolReport, OrderToolDefinition } from '../types/tool-calling'

export function useToolCalling(token: Ref<string>, logout: () => void) {
  const visible = ref(false)
  const busy = ref(false)
  const question = ref('请查询我的订单 DEMO-A001，告诉我商品和当前状态。')
  const definition = ref<OrderToolDefinition | null>(null)
  const report = ref<ToolReport | null>(null)
  const error = ref('')
  let generation = 0 // 身份变化或销毁后，旧订单结果不能回写页面。
  watch(question, () => {
    report.value = null
    error.value = ''
  })
  watch(token, () => {
    generation++
    visible.value = false
    busy.value = false
    question.value = ''
    report.value = null
    definition.value = null
    error.value = ''
  })
  onBeforeUnmount(() => {
    generation++
  })
  async function request(work: () => Promise<void>) {
    if (busy.value || !token.value) return
    const current = generation
    busy.value = true
    error.value = ''
    try {
      await work()
    } catch (caught) {
      if (current !== generation) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '订单工具实验失败'
    } finally {
      if (current === generation) busy.value = false
    }
  }
  async function open() {
    visible.value = true
    const current = generation
    await request(async () => {
      const result = await getOrderToolSchema()
      if (current === generation) definition.value = result
    })
  }
  async function run() {
    if (!question.value.trim()) return
    const current = generation
    report.value = null
    await request(async () => {
      const result = await runOrderTool(question.value.trim())
      if (current === generation) report.value = result
    })
  }
  return { visible, busy, question, definition, report, error, open, run }
}
