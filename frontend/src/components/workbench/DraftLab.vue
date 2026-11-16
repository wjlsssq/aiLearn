<script setup lang="ts">
import type { DraftReport } from '../../types/draft'
defineProps<{ busy: boolean; mode: string; report: DraftReport | null; error: string }>()
const visible = defineModel<boolean>('visible', { required: true })
const description = defineModel<string>('description', { required: true })
const emit = defineEmits<{ run: [] }>() // 展示组件只发事件，HTTP 留在 API 层。
const fields: Record<string, string> = {
  order_no: '订单号',
  issue_type: '问题类型',
  reason: '原因',
  quantity: '数量',
}
const issues = {
  return: '退货',
  exchange: '换货',
  refund: '仅退款',
  other: '其他',
  unknown: '待澄清',
}
</script>

<template>
  <div class="chain-launch">
    <span>Q06 · 从描述提取售后信息</span>
    <el-button
      size="small"
      @click="visible = true"
    >
      售后草稿
    </el-button>
  </div>
  <el-dialog
    v-model="visible"
    title="Q06 · 结构化售后草稿"
    width="min(760px, 94vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <p class="prompt-hint">
      {{
        mode === 'llm'
          ? '提取发起一次真实模型请求，可能产生费用。'
          : '模拟模式返回固定空字段样例，不进行智能提取。'
      }}本实验不读取订单或会话，不创建工单。
    </p>
    <label for="draft-description">请描述订单、遇到的问题及诉求</label>
    <el-input
      id="draft-description"
      v-model="description"
      type="textarea"
      :rows="4"
      :maxlength="2000"
      show-word-limit
      :disabled="busy"
    />
    <el-button
      type="primary"
      :loading="busy"
      :disabled="busy || !description.trim()"
      @click="emit('run')"
    >
      提取草稿
    </el-button>
    <p
      v-if="error"
      role="alert"
    >
      {{ error }}
    </p>
    <section
      v-if="report"
      class="chain-result"
    >
      <p>
        {{ report.mode === 'mock' ? '模拟样例' : '模型提取' }} · Schema
        {{ report.schema_version }} ·
        {{ report.valid ? '校验通过，尚未核验业务资格' : '校验失败，无可用草稿' }}
      </p>
      <p
        v-for="issue in report.issues"
        :key="issue"
        role="alert"
      >
        {{ issue }}
      </p>
      <template v-if="report.draft">
        <el-form label-position="top">
          <el-form-item label="订单号">
            <el-input
              :model-value="report.draft.order_no ?? '待补充'"
              readonly
            />
          </el-form-item>
          <el-form-item label="问题类型">
            <el-input
              :model-value="issues[report.draft.issue_type]"
              readonly
            />
          </el-form-item>
          <el-form-item label="原因">
            <el-input
              type="textarea"
              :model-value="report.draft.reason ?? '待补充'"
              readonly
            />
          </el-form-item>
          <el-form-item label="数量">
            <el-input
              :model-value="
                report.draft.quantity === null ? '待补充' : String(report.draft.quantity)
              "
              readonly
            />
          </el-form-item>
        </el-form>
        <p v-if="report.missing_fields.length">
          请补充{{
            report.missing_fields.map((field) => fields[field] ?? field).join('、')
          }}，在上方描述中修改后重新提取。
        </p>
        <p>这是一份待核对的草稿，尚未检查订单归属、购买数量或售后规则。</p>
        <details>
          <summary>查看校验后的 JSON</summary>
          <pre>{{ JSON.stringify(report.draft, null, 2) }}</pre>
        </details>
      </template>
    </section>
  </el-dialog>
</template>
