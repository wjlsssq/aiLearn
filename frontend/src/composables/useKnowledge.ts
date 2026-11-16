import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { ApiError } from '../api/client'
import {
  getKnowledgeExample,
  previewKnowledge,
  importKnowledge,
  listKnowledge,
  listKnowledgeVersions,
  readKnowledge,
} from '../api/knowledge'
import type {
  SplitOptions,
  SplitPreview,
  ImportResult,
  DocumentSummary,
  VersionSummary,
  KnowledgeVersion,
} from '../types/knowledge'

export function useKnowledge(token: Ref<string>, logout: () => void) {
  const visible = ref(false)
  const busy = ref(false)
  const title = ref('')
  const text = ref('')
  const first = ref<SplitOptions>({ chunk_size: 160, chunk_overlap: 30 })
  const second = ref<SplitOptions>({ chunk_size: 300, chunk_overlap: 60 })
  const previews = ref<SplitPreview[]>([])
  const imported = ref<ImportResult | null>(null)
  const documents = ref<DocumentSummary[]>([])
  const selectedDocument = ref<number | null>(null)
  const versions = ref<VersionSummary[]>([])
  const saved = ref<KnowledgeVersion | null>(null)
  const error = ref('')
  let generation = 0 // 身份变化或组件销毁后，旧响应不得写入当前界面。
  const validOptions = (o: SplitOptions) =>
    Number.isInteger(o.chunk_size) &&
    o.chunk_size >= 64 &&
    o.chunk_size <= 2000 &&
    Number.isInteger(o.chunk_overlap) &&
    o.chunk_overlap >= 0 &&
    o.chunk_overlap < o.chunk_size &&
    o.chunk_overlap <= 1000
  const valid = computed(
    () =>
      Boolean(title.value.trim()) &&
      title.value.trim().length <= 80 &&
      Boolean(text.value.trim()) &&
      Array.from(text.value).length <= 20000 &&
      validOptions(first.value) &&
      validOptions(second.value),
  )
  watch(
    [title, text, first, second],
    () => {
      previews.value = []
      imported.value = null
    },
    { deep: true },
  )
  function clear() {
    generation++
    visible.value = false
    busy.value = false
    title.value = ''
    text.value = ''
    previews.value = []
    imported.value = null
    documents.value = []
    versions.value = []
    saved.value = null
    selectedDocument.value = null
    error.value = ''
  }
  watch(token, clear)
  onBeforeUnmount(() => {
    generation++
  })

  async function action(work: (isCurrent: () => boolean) => Promise<void>) {
    if (busy.value || !token.value) return
    const current = generation
    busy.value = true
    error.value = ''
    try {
      await work(() => current === generation)
    } catch (caught) {
      if (current !== generation) return
      if (caught instanceof ApiError && caught.status === 401) logout()
      else error.value = caught instanceof Error ? caught.message : '知识库操作失败'
    } finally {
      if (current === generation) busy.value = false
    }
  }
  async function open() {
    visible.value = true
    await action(async (current) => {
      const [rows, example] = await Promise.all([
        listKnowledge(),
        !text.value ? getKnowledgeExample() : Promise.resolve(null),
      ])
      if (!current()) return
      documents.value = rows
      if (example) {
        title.value = example.title
        text.value = example.text
      }
    })
  }
  async function compare() {
    if (!valid.value) return
    await action(async (current) => {
      previews.value = []
      const body = { title: title.value.trim(), text: text.value }
      const result = await Promise.all([
        previewKnowledge({ ...body, options: { ...first.value } }),
        previewKnowledge({ ...body, options: { ...second.value } }),
      ])
      if (current()) previews.value = result // 两组都成功才展示，避免混用旧结果。
    })
  }
  async function save() {
    if (!valid.value) return
    await action(async (current) => {
      imported.value = null
      const result = await importKnowledge({
        title: title.value.trim(),
        text: text.value,
        options: { ...first.value },
      })
      if (!current()) return
      imported.value = result // 明确先确认提交，列表刷新失败不能诱导再次导入。
      saved.value = result.version
      selectedDocument.value = result.version.document_id
      versions.value = []
      documents.value = await listKnowledge().then((rows) => (current() ? rows : documents.value))
      const rows = await listKnowledgeVersions(result.version.document_id)
      if (current()) versions.value = rows
    })
  }
  async function load(id: number, revision?: number) {
    await action(async (current) => {
      saved.value = null
      versions.value = []
      imported.value = null
      const rows = await listKnowledgeVersions(id)
      if (!current()) return
      versions.value = rows
      selectedDocument.value = id
      const target = revision ?? rows.find((v) => v.active)?.revision
      if (target === undefined) return
      const result = await readKnowledge(id, target)
      if (current()) saved.value = result
    })
  }
  async function upload(file: File) {
    await action(async (current) => {
      if (!/\.(txt|md)$/i.test(file.name) || file.size > 128 * 1024)
        throw new Error('仅支持不超过 128 KB 的 UTF-8 .txt / .md 文本')
      const bytes = await file.arrayBuffer()
      let decoded: string
      try {
        decoded = new TextDecoder('utf-8', { fatal: true }).decode(bytes)
      } catch {
        throw new Error('文件不是有效 UTF-8，请转换编码后重试')
      }
      if (Array.from(decoded).length > 20000 || !decoded.trim())
        throw new Error('正文应为 1～20000 个字符，且不能全为空白')
      if (current()) {
        title.value = file.name.replace(/\.(txt|md)$/i, '').slice(0, 80)
        text.value = decoded
      }
    })
  }
  return {
    visible,
    busy,
    title,
    text,
    first,
    second,
    valid,
    previews,
    imported,
    documents,
    selectedDocument,
    versions,
    saved,
    error,
    open,
    compare,
    save,
    load,
    upload,
  }
}
