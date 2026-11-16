<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
import type { DraftReport } from '../../types/draft'
defineProps<{ busy: boolean; ready: boolean; report: DraftReport | null; error: string }>()
const visible = defineModel<boolean>('visible', { required: true })
const description = defineModel<string>('description', { required: true })
const emit = defineEmits<{ submit: []; copy: [] }>()
const types = { return: '退货', exchange: '换货', refund: '退款', other: '其他', unknown: '待确认' }
const fields: Record<string, string> = {
  order_no: '订单编号',
  issue_type: '问题类型',
  reason: '原因',
  quantity: '数量',
}
</script>
<template>
  <el-drawer
    v-model="visible"
    title="整理售后资料"
    size="min(520px, 100vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <div class="drawer-intro">
      <span class="assistant-avatar"><AppIcon name="file" /></span>
      <h3>从描述到清晰的处理资料</h3>
      <p>整理客户描述中的订单、问题和诉求，核对后可复制使用。</p>
    </div>
    <label for="draft-description">问题描述</label>
    <el-input
      id="draft-description"
      v-model="description"
      type="textarea"
      :rows="5"
      :maxlength="2000"
      :disabled="busy"
      placeholder="描述商品问题、订单编号、数量和处理诉求"
    />
    <el-button
      class="drawer-submit"
      type="primary"
      :loading="busy"
      :disabled="busy || !ready || !description.trim()"
      @click="emit('submit')"
    >
      整理资料
      <AppIcon
        name="arrow"
        :size="16"
      />
    </el-button>
    <p
      v-if="error"
      class="field-error"
      role="alert"
    >
      {{ error }}
    </p>
    <section
      v-if="report"
      class="assistant-result"
    >
      <p
        v-for="issue in report.issues"
        :key="issue"
        class="field-error"
      >
        {{ issue }}
      </p>
      <template v-if="report.draft">
        <p class="section-caption">待核对资料</p>
        <dl class="detail-list">
          <dt>订单编号</dt>
          <dd>{{ report.draft.order_no ?? '待补充' }}</dd>
          <dt>问题类型</dt>
          <dd>{{ types[report.draft.issue_type] }}</dd>
          <dt>问题原因</dt>
          <dd>{{ report.draft.reason ?? '待补充' }}</dd>
          <dt>数量</dt>
          <dd>{{ report.draft.quantity ?? '待补充' }}</dd>
        </dl>
        <p
          v-if="report.missing_fields.length"
          class="service-notice"
        >
          请补充{{ report.missing_fields.map((f) => fields[f] ?? f).join('、') }}后重新整理。
        </p>
        <p class="muted">资料尚未核对订单资格，不代表售后申请已提交。</p>
        <el-button @click="emit('copy')">复制资料</el-button>
      </template>
    </section>
  </el-drawer>
</template>
