import { defineConfig } from 'vite' // 定义开发服务器与构建配置。
import vue from '@vitejs/plugin-vue' // 编译 Vue 单文件组件。
export default defineConfig({ plugins: [vue()], server: { proxy: { '/api': 'http://127.0.0.1:8000' } } }) // 开发时同源代理 API，避免浏览器跨域。
