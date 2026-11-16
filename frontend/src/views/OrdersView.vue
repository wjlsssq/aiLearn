<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../components/common/AppIcon.vue'
import type { Order } from '../types/api'
const props = defineProps<{ orders: Order[]; ready: boolean }>()
const emit = defineEmits<{ query: [number?: string] }>()
const search = ref('')
const filtered = computed(() =>
  props.orders.filter((o) =>
    `${o.order_no} ${o.product}`.toLowerCase().includes(search.value.trim().toLowerCase()),
  ),
)
</script>
<template>
  <section class="page-content">
    <div class="page-heading">
      <div>
        <p class="eyebrow">ORDER MANAGEMENT</p>
        <h2>订单中心</h2>
        <p>查看当前账号的订单，快速获取订单信息。</p>
      </div>
      <el-button
        type="primary"
        :disabled="!ready"
        @click="emit('query')"
      >
        <AppIcon
          name="spark"
          :size="17"
        />
        订单助手
      </el-button>
    </div>
    <div class="data-card">
      <div class="data-toolbar">
        <h3>
          全部订单
          <span class="count-badge">{{ orders.length }}</span>
        </h3>
        <div class="session-search">
          <AppIcon
            name="search"
            :size="16"
          />
          <input
            v-model="search"
            aria-label="搜索订单"
            placeholder="搜索订单编号或商品"
          />
        </div>
      </div>
      <div class="desktop-orders">
        <el-table
          :data="filtered"
          empty-text="暂无匹配的订单"
        >
          <el-table-column
            prop="order_no"
            label="订单编号"
            min-width="155"
          />
          <el-table-column
            prop="product"
            label="商品"
            min-width="200"
          >
            <template #default="scope">
              <div class="table-product">
                <span class="product-icon"><AppIcon name="orders" /></span>
                <strong>{{ scope.row.product }}</strong>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="订单状态"
            min-width="150"
          >
            <template #default="scope">
              <span class="status-pill">{{ scope.row.status }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="115"
            align="right"
          >
            <template #default="scope">
              <el-button
                link
                type="primary"
                :disabled="!ready"
                @click="emit('query', scope.row.order_no)"
              >
                查询详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="mobile-orders">
        <article
          v-for="order in filtered"
          :key="order.order_no"
          class="mobile-order"
        >
          <div>
            <strong>{{ order.product }}</strong>
            <span class="status-pill">{{ order.status }}</span>
          </div>
          <p>{{ order.order_no }}</p>
          <el-button
            link
            type="primary"
            :disabled="!ready"
            @click="emit('query', order.order_no)"
          >
            查询详情
            <AppIcon
              name="arrow"
              :size="14"
            />
          </el-button>
        </article>
        <p
          v-if="!filtered.length"
          class="list-empty"
        >
          暂无匹配的订单
        </p>
      </div>
      <div class="table-footer">共 {{ filtered.length }} 条记录</div>
    </div>
  </section>
</template>
