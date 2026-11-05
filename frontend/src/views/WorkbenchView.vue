<script setup lang="ts">
import SessionSidebar from '../components/workbench/SessionSidebar.vue' // 会话导航。
import LoginForm from '../components/workbench/LoginForm.vue' // 登录表单。
import ChatPanel from '../components/workbench/ChatPanel.vue' // 对话展示与输入。
import OrderPanel from '../components/workbench/OrderPanel.vue' // 模拟订单展示。
import { useWorkbench } from '../composables/useWorkbench' // 业务状态和操作统一入口。
const {
  username,
  password,
  token,
  status,
  chatMode,
  modelName,
  modelConfigured,
  busy,
  input,
  history,
  sessions,
  orders,
  sessionId,
  newSession,
  login,
  logout,
  openSession,
  send,
} = useWorkbench() // 页面仅组合组件和绑定状态。
</script>
<template>
  <!-- 按会话导航、主内容和订单信息组织工作台。 -->
  <div class="workspace">
    <SessionSidebar
      :authenticated="Boolean(token)"
      :busy="busy"
      :sessions="sessions"
      :session-id="sessionId"
      @new-session="newSession"
      @open-session="openSession"
    />
    <main>
      <header>
        <div>
          <p class="eyebrow">CUSTOMER SUPPORT</p>
          <h1>售后服务助手</h1>
        </div>
        <div class="status">
          ● {{ status }}
          <el-button
            v-if="token"
            :disabled="busy"
            size="small"
            @click="logout"
          >
            退出登录
          </el-button>
        </div>
      </header>
      <LoginForm
        v-if="!token"
        v-model:username="username"
        v-model:password="password"
        :busy="busy"
        @submit="login"
      />
      <div
        v-else
        class="content"
      >
        <ChatPanel
          v-model:input="input"
          :busy="busy"
          :history="history"
          :chat-mode="chatMode"
          :model-name="modelName"
          :model-configured="modelConfigured"
          @send="send"
        />
        <OrderPanel
          :orders="orders"
          :busy="busy"
          @logout="logout"
        />
      </div>
    </main>
  </div>
</template>
