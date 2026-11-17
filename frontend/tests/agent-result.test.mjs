import test from 'node:test'
import assert from 'node:assert/strict'
import { isChatArtifact } from '../src/utils/agent-result.ts'

const base = {
  title: '查询结果',
  columns: ['状态', '订单数'],
  rows: [['已签收', 3]],
  truncated: false,
  missing_fields: [],
  draft: null,
}
test('聊天结果允许空表和统计值，拒绝无法展示的嵌套单元格', () => {
  assert.equal(isChatArtifact({ ...base, kind: 'orders' }), true)
  assert.equal(isChatArtifact({ ...base, kind: 'orders', rows: [] }), true)
  assert.equal(isChatArtifact({ ...base, kind: 'orders', rows: [[{ sql: '内部数据' }]] }), false)
})
test('资料结果必须包含有效字段，不把部分协议帧当成可用资料', () => {
  const value = {
    ...base,
    kind: 'draft',
    draft: { order_no: null, issue_type: 'return', reason: '损坏', quantity: 1 },
  }
  assert.equal(isChatArtifact(value), true)
  assert.equal(isChatArtifact({ ...value, draft: {} }), false)
  assert.equal(isChatArtifact({ ...value, draft: { ...value.draft, quantity: '1' } }), false)
})
