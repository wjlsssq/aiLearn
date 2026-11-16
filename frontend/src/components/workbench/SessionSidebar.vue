<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../common/AppIcon.vue'
import type { ChatSession } from '../../types/api'
const props = defineProps<{ busy: boolean; sessions: ChatSession[]; sessionId: number | null }>()
const emit = defineEmits<{ 'new-session': []; 'open-session': [id: number] }>()
const search = ref('')
const filtered = computed(() =>
  props.sessions.filter((s) => s.title.toLowerCase().includes(search.value.trim().toLowerCase())),
)
</script>
<template>
  <aside class="session-sidebar">
    <div class="session-heading">
      <h2>
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
        <span class="session-avatar">
          <AppIcon
            name="inbox"
            :size="17"
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
  </aside>
</template>
