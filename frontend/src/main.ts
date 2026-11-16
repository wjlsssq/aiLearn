import { createApp } from 'vue'
import {
  ElButton,
  ElInput,
  ElForm,
  ElFormItem,
  ElDrawer,
  ElTable,
  ElTableColumn,
  ElLoading,
} from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/workbench.css'
import App from './App.vue'

const app = createApp(App)
// 只注册业务页面实际使用的组件，避免加载整个组件库的运行时代码。
for (const [name, component] of Object.entries({
  ElButton,
  ElInput,
  ElForm,
  ElFormItem,
  ElDrawer,
  ElTable,
  ElTableColumn,
})) {
  app.component(name, component)
}
app.directive('loading', ElLoading.directive)
app.mount('#app')
