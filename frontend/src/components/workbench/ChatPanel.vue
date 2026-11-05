<script setup lang="ts">
import { ref, watch, nextTick } from 'vue' // 增量更新时按用户阅读位置滚动。
import type { ChatMessage } from '../../types/chat' // 消息正文与本地发送状态。
const props = defineProps<{
  busy: boolean
  previewBusy: boolean
  sending: boolean
  retryMessageId: string | null
  history: ChatMessage[]
  chatMode: string
  modelName: string | null
  modelConfigured: boolean
  promptValid: boolean
}>() // 父页面注入会话及模型状态，组件不读取环境配置。
const input = defineModel<string>('input', { required: true }) // 同步输入，不在组件内请求接口。
const emit = defineEmits<{ send: []; stop: []; retry: [id: string] }>() // 展示组件只发事件。
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
    <div class="panel-top">
      <span>客服对话</span>
      <el-tag
        :type="chatMode === 'llm' && modelConfigured ? 'success' : 'warning'"
        effect="plain"
      >
        {{
          chatMode === 'llm'
            ? modelConfigured
              ? `LangChain · ${modelName}`
              : '真实模型待配置'
            : '模拟响应'
        }}
      </el-tag>
    </div>
    <slot name="settings" />
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
        <div class="spark">✦</div>
        <h2>你好，有什么可以帮你？</h2>
        <p>Q02：切换回答风格，预览真正发送给模型的消息。</p>
        <el-button
          :disabled="busy"
          @click="input = '你能帮助我做哪些事情？'"
        >
          你能帮助我做哪些事情？
        </el-button>
        <p class="muted">
          {{
            chatMode === 'llm'
              ? '当前只发送本次问题；历史尚未作为模型上下文，也未接入知识库和订单工具。'
              : '当前是模拟模式。在本机 .env 配置模型并启用 CHAT_MODE=llm 后，重启后端体验真实调用。'
          }}
        </p>
        <p
          v-if="chatMode === 'llm' && !modelConfigured"
          class="muted"
        >
          请在本机 .env 补齐 API 地址、模型名和密钥，重启后端并刷新页面。
        </p>
      </div>
      <article
        v-for="(message, index) in history"
        :key="message.localId ?? index"
        class="message"
        :class="message.role"
      >
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
          <span
            class="waiting-dot"
            aria-hidden="true"
          />
          正在生成回复…
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
          v-if="message.role === 'user' && message.status === 'pending'"
          class="message-state"
        >
          发送中
        </span>
        <span
          v-if="message.role === 'user' && message.status === 'error'"
          class="message-state"
        >
          未确认保存
        </span>
      </article>
    </div>
    <el-button
      v-if="!followLatest && history.length"
      class="scroll-latest"
      size="small"
      @click="scrollToLatest"
    >
      回到最新消息
    </el-button>
    <p
      v-if="sending"
      class="generation-hint"
      role="status"
    >
      正在回复，可继续输入下一条；切换会话将停止当前回复。
    </p>
    <form
      class="composer"
      @submit.prevent="emit('send')"
    >
      <el-input
        v-model="input"
        aria-label="输入消息"
        placeholder="输入你的问题…"
        :maxlength="2000"
        :disabled="busy"
      />
      <el-button
        v-if="sending"
        native-type="button"
        @click="emit('stop')"
      >
        停止生成
      </el-button>
      <el-button
        v-else
        type="primary"
        native-type="submit"
        :disabled="busy || !modelConfigured || !promptValid || !input.trim()"
      >
        发送
      </el-button>
    </form>
  </section>
</template>
