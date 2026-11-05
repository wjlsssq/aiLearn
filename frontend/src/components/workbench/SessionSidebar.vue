<script setup lang="ts">
import type { ChatSession } from '../../types/api' // 组件只接收已加载数据。
defineProps<{
  authenticated: boolean
  busy: boolean
  sessions: ChatSession[]
  sessionId: number | null
}>() // 外部注入展示状态。
const emit = defineEmits<{ 'new-session': []; 'open-session': [id: number] }>() // 用事件通知页面，组件不请求 API。
</script>
<template>
  <aside class="sidebar">
    <div class="brand">
      S
      <span>ShopMind</span>
    </div>
    <p class="muted">智能售后客服 · 学习工作台</p>
    <div class="stage">Q02 / Prompt 与消息角色</div>
    <el-button
      v-if="authenticated"
      :disabled="busy"
      class="new-chat"
      @click="emit('new-session')"
    >
      ＋ 新建会话
    </el-button>
    <p class="section-label">会话记录</p>
    <button
      v-for="item in sessions"
      :key="item.id"
      class="session"
      :class="{ active: sessionId === item.id }"
      :disabled="busy"
      @click="emit('open-session', item.id)"
    >
      {{ item.title }}
    </button>
    <div class="sidebar-bottom">
      Vue → FastAPI → MySQL
      <br />
      每一步，都能看见。
    </div>
  </aside>
</template>
