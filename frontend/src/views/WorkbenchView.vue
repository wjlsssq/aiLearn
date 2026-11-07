<script setup lang="ts">
import SessionSidebar from '../components/workbench/SessionSidebar.vue' // 会话导航。
import LoginForm from '../components/workbench/LoginForm.vue' // 登录表单。
import ChatPanel from '../components/workbench/ChatPanel.vue' // 对话展示与输入。
import OrderPanel from '../components/workbench/OrderPanel.vue' // 模拟订单展示。
import PromptPanel from '../components/workbench/PromptPanel.vue' // Q02：模板配置与消息预览。
import ChainLab from '../components/workbench/ChainLab.vue'
import { useChainLab } from '../composables/useChainLab'
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
  previewBusy,
  sending,
  retryMessageId,
  input,
  history,
  sessions,
  orders,
  sessionId,
  storeName,
  promptStyle,
  promptPreview,
  previewVisible,
  lastPromptVersion,
  promptValid,
  newSession,
  login,
  logout,
  openSession,
  send,
  stop,
  retry,
  previewPrompt,
} = useWorkbench() // 页面仅组合组件和绑定状态。
const lab = useChainLab(token, logout)
// 解构 ref 供模板自动解包，避免组件接收到 Ref 对象。
const {
  visible: chainVisible,
  busy: chainBusy,
  method,
  first,
  second,
  prompt: chainPrompt,
  report: chainReport,
  error: chainError,
  valid: chainValid,
} = lab
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
          :preview-busy="previewBusy"
          :sending="sending"
          :retry-message-id="retryMessageId"
          :history="history"
          :chat-mode="chatMode"
          :model-name="modelName"
          :model-configured="modelConfigured"
          :prompt-valid="promptValid"
          @send="send"
          @stop="stop"
          @retry="retry"
        >
          <template #settings>
            <PromptPanel
              v-model:store-name="storeName"
              v-model:style="promptStyle"
              v-model:visible="previewVisible"
              :busy="busy"
              :preview-busy="previewBusy"
              :has-question="Boolean(input.trim())"
              :preview="promptPreview"
              :last-version="lastPromptVersion"
              @preview="previewPrompt"
            />
            <ChainLab
              v-model:visible="chainVisible"
              v-model:method="method"
              v-model:first="first"
              v-model:second="second"
              :busy="chainBusy"
              :valid="chainValid"
              :enabled="promptValid && !busy"
              :mode="chatMode"
              :prompt="chainPrompt"
              :report="chainReport"
              :error="chainError"
              @open="lab.open({ store_name: storeName, style: promptStyle }, input)"
              @run="lab.run"
            />
          </template>
        </ChatPanel>
        <OrderPanel
          :orders="orders"
          :busy="busy"
          @logout="logout"
        />
      </div>
    </main>
  </div>
</template>
