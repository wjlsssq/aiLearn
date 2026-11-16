<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
import type { Order } from '../../types/api'
defineProps<{ orders: Order[]; ready: boolean }>()
const emit = defineEmits<{ query: [orderNo?: string]; draft: [] }>()
</script>
<template>
  <aside class="context-panel">
    <div class="context-heading">
      <h2>业务上下文</h2>
      <AppIcon
        name="orders"
        :size="18"
      />
    </div>
    <section class="context-section">
      <p class="section-caption">
        订单记录
        <span>{{ orders.length }}</span>
      </p>
      <article
        v-for="order in orders"
        :key="order.order_no"
        class="context-order"
      >
        <div>
          <span class="order-small-icon">
            <AppIcon
              name="orders"
              :size="17"
            />
          </span>
          <span class="status-pill">{{ order.status }}</span>
        </div>
        <strong>{{ order.product }}</strong>
        <small>{{ order.order_no }}</small>
        <button
          :disabled="!ready"
          @click="emit('query', order.order_no)"
        >
          查询订单
          <AppIcon
            name="arrow"
            :size="14"
          />
        </button>
      </article>
      <p
        v-if="!orders.length"
        class="muted"
      >
        当前账号暂无订单。
      </p>
    </section>
    <section class="context-section">
      <p class="section-caption">快捷操作</p>
      <button
        class="context-action"
        :disabled="!ready"
        @click="emit('query')"
      >
        <AppIcon
          name="spark"
          :size="18"
        />
        <span>
          订单助手
          <small>通过自然语言查询订单</small>
        </span>
        <AppIcon
          name="chevron"
          :size="15"
        />
      </button>
      <button
        class="context-action"
        :disabled="!ready"
        @click="emit('draft')"
      >
        <AppIcon
          name="file"
          :size="18"
        />
        <span>
          整理售后资料
          <small>提取问题、原因与数量</small>
        </span>
        <AppIcon
          name="chevron"
          :size="15"
        />
      </button>
    </section>
    <div class="context-note">
      <AppIcon
        name="check"
        :size="15"
      />
      仅显示当前账号可访问的数据
    </div>
  </aside>
</template>
