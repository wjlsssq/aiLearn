<script setup lang="ts">
import type {
  SplitOptions,
  SplitPreview,
  ImportResult,
  DocumentSummary,
  VersionSummary,
  KnowledgeVersion,
} from '../../types/knowledge'
import ChunkPreview from './ChunkPreview.vue'
defineProps<{
  busy: boolean
  valid: boolean
  previews: SplitPreview[]
  imported: ImportResult | null
  documents: DocumentSummary[]
  versions: VersionSummary[]
  selectedDocument: number | null
  saved: KnowledgeVersion | null
  error: string
}>()
const visible = defineModel<boolean>('visible', { required: true })
const title = defineModel<string>('title', { required: true })
const text = defineModel<string>('text', { required: true })
const first = defineModel<SplitOptions>('first', { required: true })
const second = defineModel<SplitOptions>('second', { required: true })
const emit = defineEmits<{
  open: []
  compare: []
  save: []
  load: [id: number, revision?: number]
  upload: [file: File]
}>()
function pickFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('upload', file)
  input.value = '' // 同一文件修改后允许重新选择。
}
</script>
<template>
  <div class="chain-launch">
    <span>Q07 · 文档切分与来源追溯</span>
    <el-button
      size="small"
      @click="emit('open')"
    >
      规则知识库
    </el-button>
  </div>
  <el-dialog
    v-model="visible"
    title="Q07 · 私有教学规则库"
    width="min(1120px, 96vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <p class="prompt-hint">
      本课不调用模型，只准备文档。文档仅当前登录用户可见；预览不入库，“导入
      A”才保存。请使用合成规则。
    </p>
    <label for="knowledge-title">文档标题（同用户同标题表示同一文档）</label>
    <el-input
      id="knowledge-title"
      v-model="title"
      :maxlength="80"
      :disabled="busy"
    />
    <label class="knowledge-upload">
      选择 UTF-8 .txt / .md 文件
      <input
        type="file"
        accept=".txt,.md"
        :disabled="busy"
        @change="pickFile"
      />
    </label>
    <label for="knowledge-text">原文（最多 20000 字符；BOM 和换行在服务端规范化）</label>
    <el-input
      id="knowledge-text"
      v-model="text"
      type="textarea"
      :rows="7"
      :disabled="busy"
    />
    <div class="knowledge-grid">
      <fieldset
        v-for="name in ['A', 'B']"
        :key="name"
        :disabled="busy"
      >
        <legend>方案 {{ name }} · 字符预算</legend>
        <label>
          块大小
          <el-input-number
            :model-value="name === 'A' ? first.chunk_size : second.chunk_size"
            :min="64"
            :max="2000"
            :precision="0"
            @update:model-value="
              (value: number | undefined) =>
                name === 'A'
                  ? (first = { ...first, chunk_size: value ?? 64 })
                  : (second = { ...second, chunk_size: value ?? 64 })
            "
          />
        </label>
        <label>
          目标重叠
          <el-input-number
            :model-value="name === 'A' ? first.chunk_overlap : second.chunk_overlap"
            :min="0"
            :max="1000"
            :precision="0"
            @update:model-value="
              (value: number | undefined) =>
                name === 'A'
                  ? (first = { ...first, chunk_overlap: value ?? 0 })
                  : (second = { ...second, chunk_overlap: value ?? 0 })
            "
          />
        </label>
      </fieldset>
    </div>
    <p class="prompt-hint">重叠必须小于块大小；每组最多 512 块。修改任意输入后需重新预览。</p>
    <div class="knowledge-actions">
      <el-button
        :disabled="busy || !valid"
        @click="emit('compare')"
      >
        对比预览 A / B
      </el-button>
      <el-button
        type="primary"
        :disabled="busy || !valid"
        @click="emit('save')"
      >
        导入 A 并设为当前版本
      </el-button>
      <span
        v-if="busy"
        role="status"
      >
        处理中…
      </span>
    </div>
    <p
      v-if="imported"
      role="status"
    >
      {{ imported.reused ? '复用已有有效版本' : '导入成功' }} · 版本 {{ imported.version.revision }}
    </p>
    <p
      v-if="error"
      role="alert"
    >
      {{ error }}
    </p>
    <div class="knowledge-grid">
      <ChunkPreview
        v-for="(preview, index) in previews"
        :key="index"
        :preview="preview"
      />
    </div>
    <h3>我的文档与版本</h3>
    <p v-if="!documents.length">尚无已导入文档。</p>
    <div class="knowledge-actions">
      <el-button
        v-for="document in documents"
        :key="document.id"
        :disabled="busy"
        @click="emit('load', document.id)"
      >
        {{ document.title }} · v{{ document.active_revision }}
      </el-button>
    </div>
    <div
      v-if="selectedDocument !== null"
      class="knowledge-actions"
    >
      <el-button
        v-for="version in versions"
        :key="version.revision"
        :disabled="busy"
        @click="emit('load', selectedDocument!, version.revision)"
      >
        v{{ version.revision }} · {{ version.active ? '当前有效' : '历史' }} ·
        {{ version.chunk_count }} 块
      </el-button>
    </div>
    <template v-if="saved">
      <p>
        {{ saved.title }} · v{{ saved.revision }} ·
        {{ saved.active ? '当前有效' : '历史版本，不供后续默认检索使用' }}
      </p>
      <ChunkPreview :preview="saved" />
    </template>
  </el-dialog>
</template>
