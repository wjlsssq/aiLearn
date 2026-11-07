<script setup lang="ts">
import type { PromptOptions } from '../../types/api'
import type { ChainMethod, ChainReport } from '../../types/chain'

defineProps<{
  busy: boolean
  valid: boolean
  enabled: boolean
  mode: string
  prompt: PromptOptions
  report: ChainReport | null
  error: string
}>()
const visible = defineModel<boolean>('visible', { required: true })
const method = defineModel<ChainMethod>('method', { required: true })
const first = defineModel<string>('first', { required: true })
const second = defineModel<string>('second', { required: true })
const emit = defineEmits<{ open: []; run: [inspect: boolean] }>()
const names: Record<string, string> = {
  normalize: '规范化问题',
  prompt: '渲染消息',
  model: '调用模型',
  parse: '解析正文',
}
const states = { done: '完成', failed: '失败', skipped: '未执行' }
</script>

<template>
  <div class="chain-launch">
    <span>Q03 · 看见 Runnable 的数据流</span>
    <el-button
      :disabled="!enabled"
      size="small"
      @click="emit('open')"
    >
      流水线实验
    </el-button>
  </div>
  <el-dialog
    v-model="visible"
    title="Q03 · Runnable / LCEL 实验"
    width="min(860px, 94vw)"
    :show-close="!busy"
    :close-on-click-modal="!busy"
    :close-on-press-escape="!busy"
  >
    <p class="prompt-hint">问题 → 规范化 → Prompt → 模型 → 文本。实验不保存到会话，不读取历史。</p>
    <p>配置快照：{{ prompt.store_name }} · {{ prompt.style === 'concise' ? '简洁' : '详细' }}</p>
    <div class="chain-form">
      <label for="chain-method">执行方式</label>
      <select
        id="chain-method"
        v-model="method"
        :disabled="busy"
      >
        <option value="invoke">invoke · 一道问题</option>
        <option value="batch">batch · 两道独立问题</option>
      </select>
      <label for="chain-first">问题 1（保留空白，用于观察规范化）</label>
      <el-input
        id="chain-first"
        v-model="first"
        type="textarea"
        :rows="2"
        :maxlength="2000"
        :disabled="busy"
      />
      <template v-if="method === 'batch'">
        <label for="chain-second">问题 2</label>
        <el-input
          id="chain-second"
          v-model="second"
          type="textarea"
          :rows="2"
          :maxlength="2000"
          :disabled="busy"
        />
      </template>
      <p class="prompt-hint">
        预览不调用模型。运行将{{
          mode === 'mock'
            ? '使用离线模拟模型'
            : `发起 ${method === 'batch' ? '2' : '1'} 次真实模型请求，可能产生费用`
        }}；完成后一次展示步骤结果。普通聊天仍逐块输出。
      </p>
      <div class="chain-actions">
        <el-button
          :disabled="busy || !valid"
          @click="emit('run', true)"
        >
          预览步骤 · 无模型调用
        </el-button>
        <el-button
          type="primary"
          :disabled="busy || !valid"
          @click="emit('run', false)"
        >
          运行{{ method === 'batch' ? '两题' : '一题' }} ·
          {{ mode === 'mock' ? '模拟' : '真实模型' }}
        </el-button>
      </div>
    </div>
    <p
      v-if="busy"
      role="status"
    >
      流水线执行中，请等待结果…
    </p>
    <p
      v-if="error"
      role="alert"
      class="field-error"
    >
      {{ error }}
    </p>
    <section
      v-if="report"
      class="chain-results"
      aria-label="流水线结果"
      aria-live="polite"
    >
      <p>
        {{
          report.execution === 'inspect'
            ? '预览完成 · 未调用模型'
            : `${report.execution} 完成 · ${report.mode}`
        }}
        · Prompt v{{ report.prompt_version }}
      </p>
      <article
        v-for="result in report.results"
        :key="result.index"
        class="chain-result"
      >
        <h3>问题 {{ result.index }}</h3>
        <p>原始输入（JSON 显示空格与换行）</p>
        <pre>{{ JSON.stringify(result.original) }}</pre>
        <p
          v-if="result.error"
          class="field-error"
          role="alert"
        >
          {{ result.failed_stage }}：{{ result.error }}
        </p>
        <details
          v-for="step in result.steps"
          :key="step.name"
          :open="step.status === 'failed'"
        >
          <summary>
            {{ names[step.name] }} · {{ states[step.status] }} · {{ step.input_type }} →
            {{ step.output_type || '—' }}
          </summary>
          <pre v-if="step.output !== null">{{ step.output }}</pre>
          <p
            v-else
            class="prompt-hint"
          >
            {{
              step.status === 'skipped'
                ? '预览只执行前两步；发生错误时后续步骤也不会执行。'
                : '此步骤未生成输出。'
            }}
          </p>
        </details>
        <p
          v-if="result.reply"
          class="chain-reply"
        >
          {{ result.reply }}
        </p>
      </article>
    </section>
  </el-dialog>
</template>
