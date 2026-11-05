// 使用 Node 自带测试运行器验证分包边界，不增加前端依赖。
import test from 'node:test'
import assert from 'node:assert/strict'
import { createEventParser } from '../src/utils/sse.ts'

test('中文 UTF-8 可在任意字节处断开，多个 SSE 帧可合并到同一网络块', () => {
  const events = []
  const parse = createEventParser((event, data) => events.push({ event, data: JSON.parse(data) }))
  const payload =
    ': heartbeat\n\nevent: delta\ndata: {"text":"你好\n世界"}\n\n'.replace(
      '你好\n世界',
      '你好\\n世界',
    ) + 'event: done\ndata: {"session_id":1}\n\n'
  const bytes = new TextEncoder().encode(payload)
  const decoder = new TextDecoder()
  for (const byte of bytes) parse(decoder.decode(Uint8Array.of(byte), { stream: true }))
  parse(decoder.decode())
  assert.deepEqual(events, [
    { event: 'delta', data: { text: '你好\n世界' } },
    { event: 'done', data: { session_id: 1 } },
  ])
})

test('支持 CRLF、多个 data 行、注释与跨块的空行分隔符', () => {
  const events = []
  const parse = createEventParser((event, data) => events.push([event, data]))
  parse(': comment\r\nevent: delta\r\ndata: first\r\ndata: second\r')
  assert.deepEqual(events, [])
  parse('\n\r')
  assert.deepEqual(events, [])
  parse('\nevent: done\r\ndata: ok\r\n\r\n')
  assert.deepEqual(events, [
    ['delta', 'first\nsecond'],
    ['done', 'ok'],
  ])
})

test('未完成的帧不作为 done，错误处理交给业务流的完成标记', () => {
  const events = []
  const parse = createEventParser((event, data) => events.push([event, data]))
  parse('event: delta\ndata: token\n\nevent: done\ndata: {"session_id":')
  assert.deepEqual(events, [['delta', 'token']])
})
