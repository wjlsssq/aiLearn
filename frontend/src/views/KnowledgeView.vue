<script setup lang="ts">
import { computed, reactive, ref, type Ref } from 'vue'
import AppIcon from '../components/common/AppIcon.vue'
import { useKnowledge } from '../composables/useKnowledge'
const props = defineProps<{ token: Ref<string>; logout: () => void }>()
const knowledge = reactive(useKnowledge(props.token, props.logout))
const search = ref('')
const filtered = computed(() =>
  knowledge.documents.filter((d) =>
    d.title.toLowerCase().includes(search.value.trim().toLowerCase()),
  ),
)
function choose(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) knowledge.upload(file)
  input.value = ''
}
</script>
<template>
  <section class="page-content">
    <div class="page-heading">
      <div>
        <p class="eyebrow">SERVICE KNOWLEDGE</p>
        <h2>规则文档</h2>
        <p>集中管理当前账号的服务资料，保留每一次版本更新。</p>
      </div>
      <el-button
        type="primary"
        :disabled="knowledge.busy"
        @click="knowledge.create"
      >
        <AppIcon
          name="plus"
          :size="17"
        />
        新增文档
      </el-button>
    </div>
    <div class="info-banner">
      <AppIcon
        name="book"
        :size="18"
      />
      <span>文档已按账号隔离存储。自动问答引用尚未启用，当前可用于资料管理与查阅。</span>
    </div>
    <p
      v-if="knowledge.error"
      class="field-error"
      role="alert"
    >
      {{ knowledge.error }}
    </p>
    <p
      v-if="knowledge.notice"
      class="success-notice"
      role="status"
    >
      {{ knowledge.notice }}
    </p>
    <div class="data-card">
      <div class="data-toolbar">
        <h3>
          文档库
          <span class="count-badge">{{ knowledge.documents.length }}</span>
        </h3>
        <div class="session-search">
          <AppIcon
            name="search"
            :size="16"
          />
          <input
            v-model="search"
            aria-label="搜索文档"
            placeholder="搜索文档名称"
          />
        </div>
      </div>
      <el-table
        :data="filtered"
        v-loading="knowledge.busy"
        empty-text="暂无文档，添加服务规则或常用资料以开始"
      >
        <el-table-column
          label="文档名称"
          min-width="250"
        >
          <template #default="scope">
            <div class="table-product">
              <span class="product-icon"><AppIcon name="file" /></span>
              <strong>{{ scope.row.title }}</strong>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          label="当前版本"
          min-width="100"
        >
          <template #default="scope">v{{ scope.row.active_revision }}</template>
        </el-table-column>
        <el-table-column
          label="状态"
          min-width="100"
        >
          <template #default><span class="status-pill">已保存</span></template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="90"
          align="right"
        >
          <template #default="scope">
            <el-button
              link
              type="primary"
              :disabled="knowledge.busy"
              @click="knowledge.load(scope.row.id)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">共 {{ filtered.length }} 份文档</div>
    </div>
    <el-drawer
      v-model="knowledge.editorVisible"
      title="保存服务文档"
      size="min(620px, 100vw)"
      :show-close="!knowledge.busy"
      :close-on-click-modal="!knowledge.busy"
      :close-on-press-escape="!knowledge.busy"
    >
      <p class="muted">同名文档会更新为新版本，历史版本可继续查阅。</p>
      <el-form label-position="top">
        <el-form-item label="文档名称">
          <el-input
            v-model="knowledge.title"
            :disabled="knowledge.busy"
            :maxlength="80"
            placeholder="例如：售后处理规范"
          />
        </el-form-item>
        <el-form-item label="文档内容">
          <el-input
            v-model="knowledge.text"
            :disabled="knowledge.busy"
            type="textarea"
            :rows="14"
            placeholder="粘贴文档正文，或从文件导入"
          />
        </el-form-item>
      </el-form>
      <label class="upload-button">
        <AppIcon
          name="file"
          :size="16"
        />
        选择文件
        <input
          type="file"
          accept=".txt,.md"
          :disabled="knowledge.busy"
          @change="choose"
        />
      </label>
      <p class="muted">支持 UTF-8 TXT / Markdown，文件最大 128 KB，正文最多 20000 字符。</p>
      <p
        v-if="knowledge.error"
        class="field-error"
        role="alert"
      >
        {{ knowledge.error }}
      </p>
      <el-button
        class="drawer-submit"
        type="primary"
        v-loading="knowledge.busy"
        :disabled="
          knowledge.busy ||
          !knowledge.title.trim() ||
          !knowledge.text.trim() ||
          Array.from(knowledge.text).length > 20000
        "
        @click="knowledge.save"
      >
        保存文档
      </el-button>
    </el-drawer>
    <el-drawer
      v-model="knowledge.detailVisible"
      :title="knowledge.saved?.title ?? '文档详情'"
      size="min(700px, 100vw)"
    >
      <template v-if="knowledge.saved">
        <div class="document-toolbar">
          <span class="status-pill">{{ knowledge.saved.active ? '当前版本' : '历史版本' }}</span>
          <el-button
            v-if="knowledge.saved.active"
            :disabled="knowledge.busy"
            @click="knowledge.edit"
          >
            更新文档
          </el-button>
        </div>
        <div class="version-list">
          <button
            v-for="version in knowledge.versions"
            :key="version.revision"
            :class="{ active: version.revision === knowledge.saved.revision }"
            :disabled="knowledge.busy"
            @click="knowledge.load(knowledge.saved!.document_id, version.revision)"
          >
            v{{ version.revision }}{{ version.active ? ' · 当前' : '' }}
          </button>
        </div>
        <pre class="document-body">{{ knowledge.saved.normalized_text }}</pre>
      </template>
    </el-drawer>
  </section>
</template>
