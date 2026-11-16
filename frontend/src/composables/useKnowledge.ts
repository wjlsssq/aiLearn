import { ref, watch, onMounted, onBeforeUnmount, type Ref } from 'vue'
import { ApiError } from '../api/client'
import {
  importKnowledge,
  listKnowledge,
  listKnowledgeVersions,
  readKnowledge,
} from '../api/knowledge'
import type { DocumentSummary, KnowledgeVersion, VersionSummary } from '../types/knowledge'

export function useKnowledge(token: Ref<string>, logout: () => void) {
  const busy = ref(false),
    editorVisible = ref(false),
    detailVisible = ref(false)
  const title = ref(''),
    text = ref(''),
    error = ref(''),
    notice = ref('')
  const documents = ref<DocumentSummary[]>([]),
    versions = ref<VersionSummary[]>([])
  const saved = ref<KnowledgeVersion | null>(null)
  let generation = 0
  watch(token, () => {
    generation++
    documents.value = []
    versions.value = []
    saved.value = null
    title.value = ''
    text.value = ''
    editorVisible.value = false
    detailVisible.value = false
    busy.value = false
    error.value = ''
  })
  onBeforeUnmount(() => {
    generation++
  })
  async function action(work: (current: () => boolean) => Promise<void>) {
    if (busy.value || !token.value) return
    const request = generation
    busy.value = true
    error.value = ''
    notice.value = ''
    try {
      await work(() => request === generation)
    } catch (caught) {
      if (request !== generation) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '文档操作失败'
    } finally {
      if (request === generation) busy.value = false
    }
  }
  async function refresh() {
    await action(async (current) => {
      const rows = await listKnowledge()
      if (current()) documents.value = rows
    })
  }
  onMounted(refresh)
  function create() {
    title.value = ''
    text.value = ''
    error.value = ''
    notice.value = ''
    editorVisible.value = true
  }
  function edit() {
    if (!saved.value) return
    title.value = saved.value.title
    text.value = saved.value.normalized_text
    detailVisible.value = false
    editorVisible.value = true
  }
  async function save() {
    if (!title.value.trim() || !text.value.trim()) return
    await action(async (current) => {
      const result = await importKnowledge({
        title: title.value.trim(),
        text: text.value,
        options: { chunk_size: 300, chunk_overlap: 60 },
      })
      if (!current()) return
      editorVisible.value = false
      saved.value = result.version
      notice.value = result.reused ? '文档内容未变化，已保留当前版本' : '文档已保存'
      const rows = await listKnowledge()
      if (current()) documents.value = rows
    })
  }
  async function load(id: number, revision?: number) {
    await action(async (current) => {
      const rows = await listKnowledgeVersions(id)
      if (!current()) return
      versions.value = rows
      const target = revision ?? rows.find((v) => v.active)?.revision
      if (target === undefined) return
      const result = await readKnowledge(id, target)
      if (current()) {
        saved.value = result
        detailVisible.value = true
      }
    })
  }
  async function upload(file: File) {
    await action(async (current) => {
      if (!/\.(txt|md)$/i.test(file.name) || file.size > 128 * 1024)
        throw new Error('支持不超过 128 KB 的 UTF-8 TXT / Markdown 文件')
      let value: string
      try {
        value = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer())
      } catch {
        throw new Error('文件编码无法识别，请转换为 UTF-8 后重试')
      }
      if (!value.trim() || Array.from(value).length > 20000)
        throw new Error('文档正文应为 1～20000 个字符')
      if (current()) {
        text.value = value
        if (!title.value) title.value = file.name.replace(/\.(txt|md)$/i, '').slice(0, 80)
      }
    })
  }
  return {
    busy,
    editorVisible,
    detailVisible,
    title,
    text,
    error,
    notice,
    documents,
    versions,
    saved,
    refresh,
    create,
    edit,
    save,
    load,
    upload,
  }
}
