// 可控时钟验证首段、终态和重试隔离，不访问网络或模型。
import test from 'node:test'
import assert from 'node:assert/strict'
import { createStreamMeter } from '../src/utils/stream-metrics.ts'

test('首段只记录一次，文本块不是 token，done 后不包含清理耗时', () => {
  let time = 100
  const meter = createStreamMeter(() => time)
  time = 130
  meter.text('')
  assert.equal(meter.metrics.firstTextMs, null)
  meter.text('你好世界')
  time = 160
  meter.text(' ')
  time = 200
  meter.end()
  time = 500
  meter.end()
  meter.text('迟到的事件')
  assert.deepEqual(meter.metrics, { firstTextMs: 30, endMs: 100, textChunks: 2 })
})

test('无首字取消保留 null，重试用新时钟和全新统计', () => {
  let time = 0
  const first = createStreamMeter(() => time)
  time = 10
  first.end()
  assert.deepEqual(first.metrics, { firstTextMs: null, endMs: 10, textChunks: 0 })
  const retry = createStreamMeter(() => time)
  time = 20
  retry.text('新回复')
  assert.deepEqual(retry.metrics, { firstTextMs: 10, endMs: null, textChunks: 1 })
  assert.equal(first.metrics.firstTextMs, null)
})
