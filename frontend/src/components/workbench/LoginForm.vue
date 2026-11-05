<script setup lang="ts">
defineProps<{ busy: boolean }>() // 提交状态由业务流程控制。
const username = defineModel<string>('username', { required: true }) // 与父页面同步用户名。
const password = defineModel<string>('password', { required: true }) // 与父页面同步密码。
const emit = defineEmits<{ submit: [] }>() // 提交时通知父页面。
</script>
<template>
  <div class="login-card">
    <p class="eyebrow">WELCOME TO SHOPMIND</p>
    <h2>从一段对话开始</h2>
    <p class="muted">登录教学账号，体验有身份隔离的聊天与订单查询。</p>
    <el-form @submit.prevent="emit('submit')">
      <el-form-item label="账号">
        <el-input
          v-model="username"
          autocomplete="username"
        />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="password"
          type="password"
          show-password
          autocomplete="current-password"
        />
      </el-form-item>
      <el-button
        native-type="submit"
        type="primary"
        :loading="busy"
      >
        进入工作台
      </el-button>
    </el-form>
    <p class="muted">教学账号 alice / bob，密码均为 Learn123!</p>
  </div>
</template>
