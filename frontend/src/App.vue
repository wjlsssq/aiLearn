<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import WorkbenchView from './views/WorkbenchView.vue' // 入口仅装配全局配置与页面。
</script>
<template>
  <ElConfigProvider :locale="zhCn"><WorkbenchView /></ElConfigProvider>
</template>
