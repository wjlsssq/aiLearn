<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../common/AppIcon.vue'
import type { ChatSession } from '../../types/api'
const props = defineProps<{ busy: boolean; sessions: ChatSession[]; sessionId: number | null }>()
const emit = defineEmits<{ 'new-session': []; 'open-session': [id: number] }>()
const search = ref('')
const collapsed = ref(false) // 只折叠列表，不切换会话或取消正在生成的回复。
const sessionIcons = ['chat', 'dialogue', 'chat-lines', 'chat-dots'] // 自绘图标按会话 ID 稳定分配，不暗示业务分类。
const filtered = computed(() =>
  props.sessions.filter((s) => s.title.toLowerCase().includes(search.value.trim().toLowerCase())),
)
</script>
<template>
  <aside
    class="session-sidebar"
    :class="{ 'is-collapsed': collapsed }"
    aria-label="会话列表"
  >
    <button
      class="session-edge-toggle"
      :aria-label="collapsed ? '展开会话列表' : '折叠会话列表'"
      :title="collapsed ? '展开会话列表' : '折叠会话列表'"
      :aria-expanded="!collapsed"
      aria-controls="session-list-content"
      @click="collapsed = !collapsed"
    >
      <AppIcon
        name="chevron"
        :size="18"
      />
    </button>
    <div class="session-heading">
      <h2 v-if="!collapsed">
        我的会话
        <span>{{ sessions.length }}</span>
      </h2>

      <button
        class="icon-button"
        :disabled="busy"
        aria-label="新建会话"
        @click="emit('new-session')"
      >
        <AppIcon name="plus" />
      </button>
    </div>
    <div
      v-show="!collapsed"
      id="session-list-content"
      class="session-list-content"
    >
      <div class="session-search">
        <AppIcon
          name="search"
          :size="16"
        />
        <input
          v-model="search"
          aria-label="搜索会话"
          placeholder="搜索会话"
        />
      </div>
      <p class="section-caption">全部会话</p>
      <div class="session-list">
        <button
          v-for="session in filtered"
          :key="session.id"
          class="session-item"
          :class="{ active: sessionId === session.id }"
          :disabled="busy"
          @click="emit('open-session', session.id)"
        >
          <span
            class="session-avatar"
            :class="`session-tone-${session.id % sessionIcons.length}`"
          >
            <AppIcon
              :name="sessionIcons[session.id % sessionIcons.length]"
              :size="18"
            />
          </span>
          <span class="session-copy">
            <strong>{{ session.title }}</strong>
          </span>
          <span
            v-if="sessionId === session.id"
            class="selected-dot"
          />
        </button>
        <div
          v-if="!filtered.length"
          class="list-empty"
        >
          {{ search ? '没有匹配的会话' : '还没有会话，开始新的对话吧。' }}
        </div>
      </div>
      <button
        class="new-session-button"
        :disabled="busy"
        @click="emit('new-session')"
      >
        <AppIcon
          name="plus"
          :size="17"
        />
        新建会话
      </button>
    </div>
  </aside>
</template>
