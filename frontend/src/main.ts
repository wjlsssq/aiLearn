import { createApp } from 'vue' // 创建 Vue 应用。
import ElementPlus from 'element-plus' // 提供可交互表单与状态提示。
import 'element-plus/dist/index.css' // 加载组件基础样式。
import App from './App.vue' // 导入客服工作台。
createApp(App).use(ElementPlus).mount('#app') // 将应用挂载到页面根节点。
