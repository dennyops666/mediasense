import { config } from '@vue/test-utils'
import ElementPlus, { ElMessage, ElMessageBox, ElLoading } from './mocks/element-plus'
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from '@/router'
import { createPinia } from 'pinia'

// 配置全局插件
config.global.plugins = [
  ElementPlus,
  createPinia()
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 配置全局属性
config.global.mocks = {
  $message: ElMessage,
  $msgbox: ElMessageBox,
  $loading: ElLoading.service
}

// 配置全局组件
config.global.stubs = {
  'el-button': true,
  'el-input': true,
  'el-form': true,
  'el-form-item': true,
  'el-select': true,
  'el-option': true,
  'el-date-picker': true,
  'el-table': true,
  'el-table-column': true,
  'el-pagination': true,
  'el-dialog': true,
  'el-skeleton': true,
  'el-skeleton-item': true,
  'el-image': true,
  'el-descriptions': true,
  'el-collapse': true,
  'el-link': true,
  'el-alert': true,
  'el-empty': true
}

// 导出测试工具
export { config, router }