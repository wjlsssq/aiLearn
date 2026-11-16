<script setup lang="ts">
import AppIcon from '../common/AppIcon.vue'
defineProps<{ busy: boolean }>()
const username = defineModel<string>('username', { required: true })
const password = defineModel<string>('password', { required: true })
const emit = defineEmits<{ submit: [] }>()
</script>
<template>
  <main class="login-page">
    <section class="login-story">
      <a
        class="brand"
        href="#"
      >
        <span class="brand-symbol">
          <AppIcon
            name="spark"
            :size="23"
          />
        </span>
        <strong>ShopMind</strong>
      </a>
      <div>
        <p class="eyebrow">CUSTOMER SERVICE WORKSPACE</p>
        <h1>
          让每一次服务，
          <br />
          更进一步。
        </h1>
        <p>
          将会话、订单与服务资料汇聚一处，
          <br />
          让 AI 成为日常工作的可靠助手。
        </p>
        <div class="login-capabilities">
          <span>
            <AppIcon name="inbox" />
            持续对话
          </span>
          <span>
            <AppIcon name="orders" />
            订单协作
          </span>
          <span>
            <AppIcon name="book" />
            服务知识
          </span>
        </div>
      </div>
      <small>ShopMind · 服务工作空间</small>
    </section>
    <section class="login-form-area">
      <div class="login-card">
        <span class="login-mini-brand">
          <AppIcon name="spark" />
          ShopMind
        </span>
        <h2>登录工作空间</h2>
        <p>使用你的账号继续处理服务事务。</p>
        <el-form
          label-position="top"
          @submit.prevent="emit('submit')"
        >
          <el-form-item label="账号">
            <el-input
              v-model="username"
              placeholder="请输入账号"
              autocomplete="username"
              :disabled="busy"
            />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="password"
              placeholder="请输入密码"
              type="password"
              show-password
              autocomplete="current-password"
              :disabled="busy"
            />
          </el-form-item>
          <el-button
            class="login-submit"
            type="primary"
            native-type="submit"
            :loading="busy"
            :disabled="busy || !username.trim() || !password"
          >
            登录工作空间
            <AppIcon
              name="arrow"
              :size="17"
            />
          </el-button>
        </el-form>
        <p class="login-help">账号与访问权限由管理员管理。</p>
      </div>
    </section>
  </main>
</template>
