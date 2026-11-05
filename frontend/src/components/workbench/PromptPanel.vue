<script setup lang="ts">
import { computed } from 'vue' // 店铺名称校验属于派生展示状态。
import type { PromptPreview, PromptStyle } from '../../types/api' // 共享预览 DTO。

const props = defineProps<{
  busy: boolean
  previewBusy: boolean
  hasQuestion: boolean
  preview: PromptPreview | null
  lastVersion: string | null
}>() // 组件只展示外部状态，不持有请求逻辑。
const storeName = defineModel<string>('storeName', { required: true }) // 回传店铺名称。
const style = defineModel<PromptStyle>('style', { required: true }) // 回传风格选项。
const visible = defineModel<boolean>('visible', { required: true }) // 回传弹窗开关。
const emit = defineEmits<{ preview: [] }>() // 交给 composable 发起预览。
const nameMissing = computed(() => !storeName.value.trim()) // 与发送按钮的必填规则一致。
</script>

<template>
  <!-- 折叠配置保留聊天空间；展开后可直接观察本课变量。 -->
  <details
    class="prompt-settings"
    open
  >
    <summary>Q02 · Prompt 配置</summary>
    <div
      class="prompt-fields"
      :aria-busy="props.busy"
    >
      <div class="prompt-field">
        <label for="prompt-store-name">店铺名称（必填）</label>
        <el-input
          id="prompt-store-name"
          v-model="storeName"
          :disabled="props.busy"
          :maxlength="60"
          :aria-invalid="nameMissing"
          aria-describedby="prompt-store-hint"
          placeholder="例如：ShopMind 教学店"
        />
        <p
          id="prompt-store-hint"
          :class="nameMissing ? 'field-error' : 'prompt-hint'"
        >
          {{ nameMissing ? '请填写店铺名称，再预览或发送。' : '作为本次请求的业务标签。' }}
        </p>
      </div>
      <div class="prompt-field">
        <label for="prompt-style">回答风格</label>
        <select
          id="prompt-style"
          v-model="style"
          :disabled="props.busy"
        >
          <option value="concise">简洁 · 结论与要点</option>
          <option value="detailed">详细 · 依据与步骤</option>
        </select>
      </div>
      <el-button
        :loading="props.previewBusy"
        :disabled="props.busy || nameMissing || !props.hasQuestion"
        @click="emit('preview')"
      >
        预览消息
      </el-button>
    </div>
    <p class="prompt-hint">
      在下方输入问题后预览，无需调用模型。配置用于下一次发送。
      <span v-if="props.lastVersion">最近问答模板：v{{ props.lastVersion }}。</span>
    </p>
  </details>
  <!-- Element Plus Dialog 提供键盘关闭、焦点管理和可访问的标题。 -->
  <el-dialog
    v-model="visible"
    title="即将发送给模型的消息"
    width="min(680px, 92vw)"
    append-to-body
  >
    <template v-if="props.preview">
      <p class="prompt-dialog-caption">
        {{ props.preview.template_id }} · v{{ props.preview.version }} · 仅预览，未调用模型
      </p>
      <div class="prompt-message-list">
        <section
          v-for="message in props.preview.messages"
          :key="message.role"
          class="prompt-message"
        >
          <h3>{{ message.role }}</h3>
          <pre>{{ message.content }}</pre>
        </section>
      </div>
    </template>
    <template #footer>
      <el-button @click="visible = false">返回编辑</el-button>
    </template>
  </el-dialog>
</template>
