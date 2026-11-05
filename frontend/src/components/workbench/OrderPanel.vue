<script setup lang="ts">
import type { Order } from '../../types/api' // 订单 DTO。
defineProps<{ orders: Order[]; busy: boolean }>() // 组件只负责展示订单。
const emit = defineEmits<{ logout: [] }>() // 通知上层退出登录。
</script>
<template>
  <aside class="details">
    <div class="panel-top">
      我的订单
      <el-tag effect="plain">教学数据</el-tag>
    </div>
    <div
      v-for="order in orders"
      :key="order.order_no"
      class="order"
    >
      <small>{{ order.order_no }}</small>
      <h3>{{ order.product }}</h3>
      <p>{{ order.status }}</p>
    </div>
    <p class="muted">这里只展示当前登录用户的订单。切换 alice / bob 可观察数据隔离。</p>
    <el-button
      :disabled="busy"
      @click="emit('logout')"
    >
      退出登录
    </el-button>
  </aside>
</template>
