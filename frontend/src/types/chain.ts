import type { PromptOptions, PromptPreview } from './api'

export type ChainMethod = 'invoke' | 'batch'
export interface ChainInput {
  questions: string[]
  method: ChainMethod
  prompt: PromptOptions
}
export interface ChainReport {
  execution: 'inspect' | ChainMethod
  mode: string
  model: string | null
  prompt_version: string
  results: {
    index: number
    original: string
    normalized: string | null
    messages: PromptPreview['messages']
    reply: string | null
    error: string | null
    failed_stage: string | null
    steps: {
      name: string
      status: 'done' | 'failed' | 'skipped'
      input_type: string
      output_type: string | null
      output: string | null
    }[]
  }[]
}
