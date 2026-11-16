// Q05：只测本机观察到的事件，不将网络块数当作 token 数。
export interface StreamMetrics {
  firstTextMs: number | null // 请求开始到首个非空正文块；尚未收到时为 null。
  endMs: number | null // 收到 done、失败或取消；不是供应商纯推理耗时。
  textChunks: number // 非空 delta 数量，空格块也计数。
}

export function createStreamMeter(now: () => number = () => performance.now()) {
  const startedAt = now() // 每次重试创建新实例，使用单调时钟计算时间差。
  const metrics: StreamMetrics = { firstTextMs: null, endMs: null, textChunks: 0 }
  return {
    metrics,
    text(value: string) {
      if (!value || metrics.endMs !== null) return // 空元数据和终态后的事件不计数。
      metrics.firstTextMs ??= Math.max(0, now() - startedAt) // 后续块不覆盖首次时间。
      metrics.textChunks += 1
    },
    end() {
      metrics.endMs ??= Math.max(0, now() - startedAt) // done 后的清理不延长测量。
    },
  }
}
