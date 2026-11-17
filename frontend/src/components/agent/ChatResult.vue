<script setup lang="ts">
import type { ChatArtifact } from '../../types/agent'
defineProps<{ result: ChatArtifact }>()
const columnLabels: Record<string, string> = {
  order_no: '订单编号',
  product: '商品',
  status: '状态',
}
const issueLabels = {
  return: '退货',
  exchange: '换货',
  refund: '退款',
  other: '其他',
  unknown: '待确认',
}
const fieldLabels: Record<string, string> = {
  order_no: '订单编号',
  reason: '原因',
  quantity: '数量',
  issue_type: '问题类型',
}
</script>
<template>
  <section
    class="chat-result"
    :aria-label="result.title"
  >
    <header>
      <strong>{{ result.title }}</strong>
      <span v-if="result.kind === 'orders'">{{ result.rows.length }} 条结果</span>
    </header>
    <template v-if="result.kind === 'orders'">
      <div
        v-if="result.rows.length"
        class="chat-result-scroll"
      >
        <table>
          <thead>
            <tr>
              <th
                v-for="(column, index) in result.columns"
                :key="index"
              >
                {{ columnLabels[column] ?? column }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, rowIndex) in result.rows"
              :key="rowIndex"
            >
              <td
                v-for="(cell, index) in row"
                :key="index"
              >
                {{ cell ?? '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else>当前账号没有符合条件的订单。</p>
      <small v-if="result.truncated">仅显示部分结果，可补充条件缩小范围。</small>
    </template>
    <dl v-else-if="result.draft">
      <div>
        <dt>订单编号</dt>
        <dd>{{ result.draft.order_no ?? '待补充' }}</dd>
      </div>
      <div>
        <dt>问题类型</dt>
        <dd>{{ issueLabels[result.draft.issue_type] }}</dd>
      </div>
      <div>
        <dt>原因</dt>
        <dd>{{ result.draft.reason ?? '待补充' }}</dd>
      </div>
      <div>
        <dt>数量</dt>
        <dd>{{ result.draft.quantity ?? '待补充' }}</dd>
      </div>
    </dl>
    <small v-if="result.kind === 'draft'">
      资料仅供核对，尚未创建售后单。
      <template v-if="result.missing_fields.length">
        待补充：{{ result.missing_fields.map((field) => fieldLabels[field] ?? field).join('、') }}。
      </template>
    </small>
  </section>
</template>
