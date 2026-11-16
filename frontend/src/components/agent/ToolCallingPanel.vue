<script setup lang="ts">
import type { ToolReport, OrderToolDefinition } from '../../types/tool-calling'
defineProps<{
  busy: boolean
  mode: string
  definition: OrderToolDefinition | null
  report: ToolReport | null
  error: string
}>()
const visible = defineModel<boolean>('visible', { required: true })
const question = defineModel<string>('question', { required: true })
const emit = defineEmits<{ open: []; run: [] }>() // 组件不发 HTTP，不读取当前用户凭据。
const states = { done: '完成', failed: '失败', blocked: '已阻止' }
const reportStates = { complete: '流程完成', failed: '流程含失败', blocked: '执行被阻止' }
</script>
<template>
  <div class="chain-launch">
    <span>Q12 · Agent 基础：模型提议 → 服务端执行</span>
    <el-button
      size="small"
      @click="emit('open')"
    >
      订单工具实验
    </el-button>
  </div>
  <el-dialog
    v-model="visible"
    title="Q12 · Tool Calling 订单实验"
    width="min(840px, 94vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <p class="prompt-hint">
      {{
        mode === 'llm'
          ? '最多两次真实模型请求，可能产生费用。'
          : '模拟模式固定查询 DEMO-A001，不理解任意问题；订单卡片仍来自当前用户的真实教学 MySQL。'
      }}本课至多执行一个只读工具，不保存会话、不退款、不建单。
    </p>
    <details v-if="definition">
      <summary>服务端工具定义（适配器会转换为供应商格式）</summary>
      <p>{{ definition.name }}：{{ definition.description }}</p>
      <pre class="tool-json">{{ JSON.stringify(definition.parameters, null, 2) }}</pre>
      <p>工具参数不含用户 ID；认证身份由服务端注入。</p>
    </details>
    <label for="tool-question">订单问题</label>
    <el-input
      id="tool-question"
      v-model="question"
      :disabled="busy"
      type="textarea"
      :rows="3"
      :maxlength="2000"
      show-word-limit
    />
    <div class="knowledge-actions">
      <el-button
        type="primary"
        :loading="busy"
        :disabled="busy || !question.trim()"
        @click="emit('run')"
      >
        运行工具实验
      </el-button>
      <el-button
        :disabled="busy"
        @click="question = '请查询我的订单 DEMO-A001。'"
      >
        查 A001
      </el-button>
      <el-button
        :disabled="busy"
        @click="question = '请查询订单 DEMO-B001。'"
      >
        查 B001
      </el-button>
      <el-button
        :disabled="busy"
        @click="question = '帮我查订单状态。'"
      >
        缺少订单号
      </el-button>
    </div>
    <p
      v-if="error"
      role="alert"
    >
      {{ error }}
    </p>
    <section
      v-if="report"
      class="tool-report"
    >
      <p>
        {{ report.mode === 'mock' ? '模拟协议流程' : '真实模型调用' }} ·
        {{ reportStates[report.status] }} · {{ report.model_calls }} 次模型请求 /
        {{ report.tool_executions }} 次工具执行
      </p>
      <ol>
        <li
          v-for="(step, index) in report.steps"
          :key="index"
        >
          <h3>{{ index + 1 }}. {{ step.label }} · {{ states[step.status] }}</h3>
          <p>{{ step.message }}</p>
          <template v-if="step.stage === 'tool'">
            <p>工具：{{ step.name }} · call_id：{{ step.call_id }}</p>
            <pre class="tool-json">{{ JSON.stringify(step.arguments, null, 2) }}</pre>
            <article
              v-if="step.result?.order"
              class="tool-order"
            >
              <p>MySQL 教学订单：{{ step.result.order.order_no }}</p>
              <p>{{ step.result.order.product }} · {{ step.result.order.status }}</p>
              <p>{{ step.result.logistics }}</p>
            </article>
            <p v-else>{{ step.result?.message }}</p>
          </template>
        </li>
      </ol>
      <template v-if="report.answer">
        <h3>最终答复</h3>
        <p class="chain-reply">{{ report.answer }}</p>
      </template>
      <p class="prompt-hint">
        订单卡片是后端查询结果，最终文字由模型生成。未执行工具时不代表查过订单；请核对卡片，不能凭生成文字认定业务事实。
      </p>
    </section>
  </el-dialog>
</template>
