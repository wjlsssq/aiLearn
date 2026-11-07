import { request } from './client'
import type { ChainInput, ChainReport } from '../types/chain'

export const runChain = (body: ChainInput, inspect: boolean) =>
  request<ChainReport>(inspect ? '/chains/inspect' : '/chains/run', body)
