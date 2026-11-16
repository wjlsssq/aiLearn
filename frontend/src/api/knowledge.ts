import { request } from './client'
import type {
  KnowledgeInput,
  SplitPreview,
  ImportResult,
  DocumentSummary,
  VersionSummary,
  KnowledgeVersion,
} from '../types/knowledge'

export const getKnowledgeExample = () => request<KnowledgeInput>('/knowledge/example')
export const previewKnowledge = (body: KnowledgeInput) =>
  request<SplitPreview>('/knowledge/preview', body)
export const importKnowledge = (body: KnowledgeInput) =>
  request<ImportResult>('/knowledge/import', body)
export const listKnowledge = () => request<DocumentSummary[]>('/knowledge/documents')
export const listKnowledgeVersions = (id: number) =>
  request<VersionSummary[]>(`/knowledge/documents/${id}/versions`)
export const readKnowledge = (id: number, revision: number) =>
  request<KnowledgeVersion>(`/knowledge/documents/${id}/versions/${revision}`)
