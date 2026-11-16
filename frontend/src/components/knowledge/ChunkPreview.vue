<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { SplitPreview } from '../../types/knowledge'
const props = defineProps<{ preview: SplitPreview }>()
const selected = ref(1)
watch(
  () => props.preview,
  () => {
    selected.value = 1
  },
)
const chunk = computed(() => props.preview.chunks.find((c) => c.ordinal === selected.value))
const source = computed(() => {
  const points = Array.from(props.preview.normalized_text) // 后端偏移是码点，正确处理 emoji。
  const current = chunk.value
  return current
    ? {
        before: points.slice(0, current.start).join(''),
        selected: points.slice(current.start, current.end).join(''),
        after: points.slice(current.end).join(''),
      }
    : null
})
</script>
<template>
  <section class="knowledge-preview">
    <p>
      {{ preview.chunks.length }} 块 · size {{ preview.options.chunk_size }} / overlap
      {{ preview.options.chunk_overlap }}（字符）
    </p>
    <p class="knowledge-hash">
      {{ preview.splitter_version }} · 内容 SHA256：{{ preview.content_hash }}
    </p>
    <label>
      定位分块
      <select v-model="selected">
        <option
          v-for="item in preview.chunks"
          :key="item.ordinal"
          :value="item.ordinal"
        >
          #{{ item.ordinal }} · 行 {{ item.start_line }}–{{ item.end_line }}
        </option>
      </select>
    </label>
    <template v-if="chunk && source">
      <p>
        码点范围 [{{ chunk.start }}, {{ chunk.end }}) · {{ Array.from(chunk.text).length }} 字符 ·
        起点标题：{{ chunk.heading ?? '无' }}
      </p>
      <pre class="knowledge-chunk">{{ chunk.text }}</pre>
      <details>
        <summary>在规范化原文中查看高亮</summary>
        <pre>{{ source.before }}<mark>{{ source.selected }}</mark>{{ source.after }}</pre>
      </details>
    </template>
  </section>
</template>
