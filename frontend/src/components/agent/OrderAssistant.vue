<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
import type { OrderAssistantResponse } from '../../types/api'
defineProps<{
  busy: boolean
  ready: boolean
  result: OrderAssistantResponse | null
  error: string
}>()
const visible = defineModel<boolean>('visible', { required: true })
const question = defineModel<string>('question', { required: true })
const emit = defineEmits<{ submit: [] }>()
</script>
<template>
  <el-drawer
    v-model="visible"
    title="订单助手"
    size="min(520px, 100vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <div class="drawer-intro">
      <span class="assistant-avatar"><AppIcon name="spark" /></span>
      <h3>让订单信息更清晰</h3>
      <p>输入订单编号与查询需求，获取当前账号可访问的订单信息。</p>
    </div>
    <label for="order-question">查询内容</label>
    <el-input
      id="order-question"
      v-model="question"
      type="textarea"
      :rows="4"
      :disabled="busy"
      :maxlength="2000"
      placeholder="例如：查询订单编号及当前状态"
    />
    <el-button
      class="drawer-submit"
      type="primary"
      :loading="busy"
      :disabled="busy || !ready || !question.trim()"
      @click="emit('submit')"
    >
      查询订单
      <AppIcon
        name="arrow"
        :size="16"
      />
    </el-button>
    <p
      v-if="!ready"
      class="service-notice"
    >
      智能服务尚未启用，请联系管理员。
    </p>
    <p
      v-if="error"
      class="field-error"
      role="alert"
    >
      {{ error }}
    </p>
    <section
      v-if="result"
      class="assistant-result"
    >
      <p class="section-caption">查询结果</p>
      <article
        v-if="result.order"
        class="result-order"
      >
        <span class="status-pill">{{ result.order.status }}</span>
        <h3>{{ result.order.product }}</h3>
        <p>{{ result.order.order_no }}</p>
      </article>
      <p v-if="result.status !== 'complete' || !result.answer">{{ result.message }}</p>
      <p
        v-if="result.answer"
        class="answer-text"
      >
        {{ result.answer }}
      </p>
    </section>
  </el-drawer>
</template>
