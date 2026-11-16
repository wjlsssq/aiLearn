<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
import { ref, watch, nextTick } from 'vue' // 增量更新时按用户阅读位置滚动。
import type { ChatMessage } from '../../types/chat' // 消息正文与本地发送状态。
const props = defineProps<{
  busy: boolean
  sending: boolean
  retryMessageId: string | null
  history: ChatMessage[]
  ready: boolean
  title: string
}>() // 父页面注入会话及模型状态，组件不读取环境配置。
const input = defineModel<string>('input', { required: true }) // 同步输入，不在组件内请求接口。
const emit = defineEmits<{
  send: []
  stop: []
  retry: [id: string]
  'toggle-context': []
  draft: []
}>() // 展示组件只发事件。
const messagesElement = ref<HTMLElement | null>(null)
const followLatest = ref(true) // 用户向上阅读后不强制拉回底部。
function scrollToLatest() {
  const element = messagesElement.value
  if (element) element.scrollTop = element.scrollHeight
  followLatest.value = true
}
function trackScroll() {
  const element = messagesElement.value
  if (element)
    followLatest.value = element.scrollHeight - element.scrollTop - element.clientHeight < 64
}
watch(
  [() => props.history, () => props.history.length],
  async () => {
    await nextTick()
    scrollToLatest() // 切换历史或发送新问题时定位到最新消息。
  },
  { flush: 'post' },
)
watch(
  () => props.history.at(-1)?.content,
  async () => {
    await nextTick()
    if (followLatest.value) scrollToLatest() // 布局更新后再确认，尊重用户刚发生的滚动。
  },
  { flush: 'post' },
)
</script>
<template>
  <section class="chat-panel">
    <div class="chat-header">
      <div class="chat-title">
        <span class="assistant-avatar"><AppIcon name="spark" /></span>
        <div>
          <h2>{{ title }}</h2>
          <small>
            <i class="live-dot" />
            ShopMind 服务助手
          </small>
        </div>
      </div>
      <button
        class="icon-button"
        aria-label="切换订单上下文"
        @click="emit('toggle-context')"
      >
        <AppIcon name="orders" />
      </button>
    </div>
    <div
      v-if="!ready"
      class="service-notice"
    >
      智能服务尚未启用，请联系管理员完成配置。历史会话仍可查看。
    </div>
    <div
      ref="messagesElement"
      class="messages"
      role="log"
      aria-label="对话消息"
      tabindex="0"
      aria-live="polite"
      aria-relevant="additions"
      @scroll="trackScroll"
    >
      <div
        v-if="!history.length"
        class="welcome"
      >
        <span class="welcome-symbol">
          <AppIcon
            name="spark"
            :size="30"
          />
        </span>
        <p class="eyebrow">YOUR SERVICE COPILOT</p>
        <h2>你好，今天需要处理什么？</h2>
        <p>梳理服务问题，准备回复，让每个下一步更清晰。</p>
        <div class="suggestion-grid">
          <button @click="input = '帮我整理一份商品故障需要补充的信息清单。'">
            <AppIcon name="file" />
            <strong>梳理问题信息</strong>
            <span>整理客户描述与待补充材料</span>
            <AppIcon
              name="arrow"
              :size="16"
            />
          </button>
          <button @click="input = '帮我写一段专业、友好的售后沟通回复。'">
            <AppIcon name="inbox" />
            <strong>准备服务回复</strong>
            <span>将沟通意图整理为清晰表达</span>
            <AppIcon
              name="arrow"
              :size="16"
            />
          </button>
        </div>
      </div>
      <article
        v-for="(message, index) in history"
        :key="message.localId ?? index"
        class="message"
        :class="message.role"
      >
        <span class="message-avatar">
          <AppIcon
            v-if="message.role !== 'user'"
            name="spark"
            :size="17"
          />
          <span v-else>我</span>
        </span>
        <div class="message-body">
          <span class="role">{{ message.role === 'user' ? '你' : 'ShopMind' }}</span>
          <p v-if="message.content">
            {{ message.content }}
            <span
              v-if="message.status === 'streaming'"
              class="stream-cursor"
              aria-hidden="true"
            >
              ▍
            </span>
          </p>
          <p
            v-else-if="message.status === 'pending'"
            class="reply-pending"
            role="status"
          >
            <span class="waiting-dot" />
            正在准备回复…
          </p>
          <div
            v-if="message.role === 'assistant' && message.error"
            class="message-feedback"
            role="status"
          >
            <span>{{ message.error }}</span>
            <el-button
              v-if="message.localId === retryMessageId"
              :disabled="sending || busy"
              size="small"
              @click="emit('retry', message.localId!)"
            >
              {{ message.status === 'stopped' ? '重新生成' : '重试' }}
            </el-button>
          </div>
          <span
            v-if="message.role === 'user' && message.status === 'error'"
            class="message-state"
          >
            保存状态待确认，请重新打开会话核对
          </span>
        </div>
      </article>
    </div>
    <button
      v-if="!followLatest && history.length"
      class="scroll-latest"
      @click="scrollToLatest"
    >
      回到最新消息 ↓
    </button>
    <div class="composer-area">
      <div class="composer-tools">
        <button
          :disabled="!ready"
          @click="emit('draft')"
        >
          <AppIcon
            name="file"
            :size="15"
          />
          整理售后资料
        </button>
        <span v-if="sending">正在回复，可继续编辑下一条消息</span>
      </div>
      <form
        class="composer"
        @submit.prevent="emit('send')"
      >
        <el-input
          v-model="input"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 6 }"
          aria-label="输入消息"
          placeholder="描述需要处理的问题…"
          :maxlength="2000"
          :disabled="busy"
          @keydown.enter.exact.prevent="emit('send')"
        />
        <div class="composer-bottom">
          <span>Enter 发送 · Shift + Enter 换行</span>
          <button
            v-if="sending"
            type="button"
            class="send-button stop-button"
            @click="emit('stop')"
          >
            <AppIcon
              name="stop"
              :size="15"
            />
            停止生成
          </button>
          <button
            v-else
            type="submit"
            class="send-button"
            :disabled="busy || !ready || !input.trim()"
          >
            发送
            <AppIcon
              name="arrow"
              :size="16"
            />
          </button>
        </div>
      </form>
      <p class="composer-disclaimer">AI 回复供参考，订单与售后事项请核对业务记录。</p>
    </div>
  </section>
</template>
