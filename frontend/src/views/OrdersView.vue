<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../components/common/AppIcon.vue'
import type { Order } from '../types/api'
const props = defineProps<{ orders: Order[]; ready: boolean }>()
const emit = defineEmits<{ query: [number?: string] }>()
const search = ref('')
const money = (value: string | null) => (value == null ? '未记录' : `¥${Number(value).toFixed(2)}`)
const time = (value: string | null) => value?.replace('T', ' ') ?? '未记录'
const destination = (order: Order) =>
  [order.province, order.city, order.district, order.address].filter(Boolean).join('') || '未记录'
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
        在聊天中查询
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
            label="数量 / 单价"
            min-width="130"
          >
            <template #default="{ row }">
              {{ row.quantity ?? '—' }} / {{ money(row.unit_price) }}
            </template>
          </el-table-column>
          <el-table-column
            label="应付 / 实付"
            min-width="165"
          >
            <template #default="{ row }">
              {{ money(row.total_amount) }} / {{ money(row.paid_amount) }}
            </template>
          </el-table-column>
          <el-table-column
            label="下单时间"
            min-width="175"
          >
            <template #default="{ row }">{{ time(row.created_at) }}</template>
          </el-table-column>
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="order-detail">
                <p>
                  收货人：{{ row.recipient_name ?? '未记录' }} ·
                  {{ row.recipient_phone ?? '未记录' }}
                </p>
                <p>收货地址：{{ destination(row) }}</p>
                <p>
                  优惠：{{ money(row.discount_amount) }} · 运费：{{ money(row.shipping_fee) }} ·
                  已退：{{ money(row.refund_amount) }}
                </p>
                <p>
                  付款：{{ time(row.paid_at) }} · 发货：{{ time(row.shipped_at) }} · 签收：{{
                    time(row.delivered_at)
                  }}
                </p>
                <p>
                  物流：{{ row.shipping_company ?? '未发货' }} · {{ row.tracking_no ?? '暂无运单' }}
                </p>
              </div>
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
          <p>{{ order.order_no }} · {{ order.quantity ?? '—' }} 件</p>
          <p>实付 {{ money(order.paid_amount) }} · 下单 {{ time(order.created_at) }}</p>
          <details class="order-detail">
            <summary>订单明细与收货信息</summary>
            <p>单价 {{ money(order.unit_price) }} · 应付 {{ money(order.total_amount) }}</p>
            <p>
              优惠 {{ money(order.discount_amount) }} · 运费 {{ money(order.shipping_fee) }} · 已退
              {{ money(order.refund_amount) }}
            </p>
            <p>{{ order.recipient_name ?? '未记录' }} · {{ order.recipient_phone ?? '未记录' }}</p>
            <p>{{ destination(order) }}</p>
            <p>
              付款 {{ time(order.paid_at) }} · 发货 {{ time(order.shipped_at) }} · 签收
              {{ time(order.delivered_at) }}
            </p>
            <p>{{ order.shipping_company ?? '未发货' }} · {{ order.tracking_no ?? '暂无运单' }}</p>
          </details>
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
