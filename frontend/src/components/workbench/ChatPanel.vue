<script setup lang="ts">
import type { Message } from '../../types/api' // 消息 DTO。
defineProps<{
  busy: boolean
  previewBusy: boolean
  history: Message[]
  chatMode: string
  modelName: string | null
  modelConfigured: boolean
  promptValid: boolean
}>() // 父页面注入会话及模型状态，组件不读取环境配置。
const input = defineModel<string>('input', { required: true }) // 同步输入，不在组件内请求接口。
const emit = defineEmits<{ send: [] }>() // 点击发送或回车时通知业务流程。
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
      class="messages"
      aria-live="polite"
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
        :key="index"
        class="message"
        :class="message.role"
      >
        <span class="role">{{ message.role === 'user' ? '你' : 'ShopMind' }}</span>
        <p>{{ message.content }}</p>
      </article>
    </div>
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
        type="primary"
        native-type="submit"
        :loading="busy && !previewBusy"
        :disabled="busy || !modelConfigured || !promptValid"
      >
        发送
      </el-button>
    </form>
  </section>
</template>
