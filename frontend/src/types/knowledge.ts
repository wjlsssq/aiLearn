// 偏移按服务端 Unicode 码点计数，不能直接当 JS UTF-16 下标。
export interface SplitOptions {
  chunk_size: number
  chunk_overlap: number
}
export interface KnowledgeInput {
  title: string
  text: string
  options: SplitOptions
}
export interface KnowledgeChunk {
  ordinal: number
  text: string
  start: number
  end: number
  start_line: number
  end_line: number
  heading: string | null
}
export interface SplitPreview {
  title: string
  normalized_text: string
  content_hash: string
  fingerprint: string
  splitter_version: string
  options: SplitOptions
  chunks: KnowledgeChunk[]
}
export interface KnowledgeVersion extends SplitPreview {
  document_id: number
  revision: number
  active: boolean
}
export interface ImportResult {
  reused: boolean
  version: KnowledgeVersion
}
export interface DocumentSummary {
  id: number
  title: string
  active_revision: number
}
export interface VersionSummary {
  revision: number
  active: boolean
  content_hash: string
  chunk_count: number
  options: SplitOptions
}
