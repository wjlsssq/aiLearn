<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import AppIcon from '../components/common/AppIcon.vue'
import SessionSidebar from '../components/workbench/SessionSidebar.vue'
import LoginForm from '../components/workbench/LoginForm.vue'
import ChatPanel from '../components/workbench/ChatPanel.vue'
import OrderPanel from '../components/workbench/OrderPanel.vue'
import OrdersView from './OrdersView.vue'
import KnowledgeView from './KnowledgeView.vue'
import { useWorkbench } from '../composables/useWorkbench'
const state = useWorkbench()
const work = reactive(state)
const page = ref<'conversations' | 'orders' | 'knowledge'>('conversations')
const mobileNav = ref(false)
const contextVisible = ref(true)
const titles = { conversations: '会话工作台', orders: '订单中心', knowledge: '规则文档' }
const sessionTitle = computed(
  () => work.sessions.find((s) => s.id === work.sessionId)?.title ?? '新会话',
)
watch(state.token, () => {
  page.value = 'conversations'
  mobileNav.value = false
})
function navigate(next: typeof page.value) {
  page.value = next
  mobileNav.value = false
}
function toggleContext() {
  if (window.matchMedia('(max-width: 1050px)').matches) page.value = 'orders'
  else contextVisible.value = !contextVisible.value
}
function askOrder(number?: string) {
  page.value = 'conversations'
  work.input = number ? `请查询订单 ${number} 的当前状态。` : '请按状态统计我的订单数量。'
}
function prepareDraft() {
  page.value = 'conversations'
  work.input = work.input.trim() ? `请整理以下售后资料：\n${work.input}` : '请帮我整理售后资料。'
}
</script>
<template>
  <LoginForm
    v-if="!work.token"
    v-model:username="work.username"
    v-model:password="work.password"
    :busy="work.busy"
    @submit="work.login"
  />
  <div
    v-else
    class="app-shell"
  >
    <nav
      class="app-nav"
      :class="{ 'is-open': mobileNav }"
      aria-label="业务导航"
    >
      <a
        class="brand"
        href="#"
        @click.prevent="navigate('conversations')"
      >
        <span class="brand-symbol">
          <AppIcon
            name="spark"
            :size="23"
          />
        </span>
        <strong>
          ShopMind
          <span>服务工作空间</span>
        </strong>
      </a>
      <div class="workspace-label">
        <span class="workspace-avatar">S</span>
        <div>
          服务工作台
          <small>WORKSPACE</small>
        </div>
        <span class="workspace-dot" />
      </div>
      <p class="nav-caption">工作空间</p>
      <button
        :class="{ active: page === 'conversations' }"
        @click="navigate('conversations')"
      >
        <AppIcon name="inbox" />
        会话工作台
        <span class="nav-count">{{ work.sessions.length }}</span>
      </button>
      <button
        :class="{ active: page === 'orders' }"
        @click="navigate('orders')"
      >
        <AppIcon name="orders" />
        订单中心
      </button>
      <button
        :class="{ active: page === 'knowledge' }"
        @click="navigate('knowledge')"
      >
        <AppIcon name="book" />
        规则文档
      </button>
      <div class="nav-bottom">
        <span class="account-avatar">{{ work.currentUser.slice(0, 1).toUpperCase() || 'U' }}</span>
        <div>
          <strong>{{ work.currentUser || '当前账号' }}</strong>
          <small>已登录</small>
        </div>
        <button
          class="icon-button"
          aria-label="退出登录"
          @click="work.logout"
        >
          <AppIcon
            name="logout"
            :size="18"
          />
        </button>
      </div>
    </nav>
    <button
      v-if="mobileNav"
      class="nav-mask"
      aria-label="关闭导航"
      @click="mobileNav = false"
    />
    <main class="app-main">
      <header class="app-header">
        <div class="header-title">
          <button
            class="icon-button mobile-menu"
            aria-label="打开导航"
            @click="mobileNav = true"
          >
            <AppIcon name="menu" />
          </button>
          <span>工作空间</span>
          <AppIcon
            name="chevron"
            :size="14"
          />
          <h1>{{ titles[page] }}</h1>
        </div>
        <div class="connection-status">
          <i :class="{ connected: work.modelConfigured }" />
          {{ work.status }}
        </div>
      </header>
      <div
        v-if="page === 'conversations'"
        class="conversation-workspace"
      >
        <SessionSidebar
          :busy="work.busy"
          :sessions="work.sessions"
          :session-id="work.sessionId"
          @new-session="work.newSession"
          @open-session="work.openSession"
        />
        <ChatPanel
          v-model:input="work.input"
          :title="sessionTitle"
          :busy="work.busy"
          :sending="work.sending"
          :retry-message-id="work.retryMessageId"
          :history="work.history"
          :ready="work.modelConfigured"
          @send="work.send"
          @stop="work.stop"
          @retry="work.retry"
          @toggle-context="toggleContext"
          @draft="prepareDraft"
        />
        <OrderPanel
          v-if="contextVisible"
          :orders="work.orders"
          :ready="work.modelConfigured"
          @query="askOrder"
          @draft="prepareDraft"
        />
      </div>
      <OrdersView
        v-else-if="page === 'orders'"
        :orders="work.orders"
        :ready="work.modelConfigured"
        @query="askOrder"
      />
      <KnowledgeView
        v-else
        :token="state.token"
        :logout="work.logout"
      />
    </main>
  </div>
</template>
