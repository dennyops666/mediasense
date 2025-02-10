import { config } from '@vue/test-utils'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { vi } from 'vitest'
import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

// 创建全局 Pinia 实例
const pinia = createPinia()

// 创建一个 Vue 应用实例用于全局插件注册
const app = createApp({})

// 注册 Element Plus
app.use(ElementPlus)

// 注册 Pinia
app.use(pinia)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 配置全局组件
config.global.plugins = [pinia]

// 模拟 Element Plus 的消息组件
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue('confirm'),
      alert: vi.fn().mockResolvedValue('ok')
    },
    ElLoading: {
      service: vi.fn().mockReturnValue({
        close: vi.fn()
      })
    }
  }
})

// 模拟 canvas
vi.mock('canvas', () => ({
  default: {
    getContext: vi.fn().mockReturnValue({
      measureText: vi.fn().mockReturnValue({ width: 100 }),
      fillText: vi.fn(),
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      getImageData: vi.fn().mockReturnValue({ data: new Uint8Array(100) }),
      putImageData: vi.fn(),
      createImageData: vi.fn(),
      setTransform: vi.fn(),
      drawImage: vi.fn(),
      save: vi.fn(),
      restore: vi.fn(),
      scale: vi.fn(),
      rotate: vi.fn(),
      translate: vi.fn(),
      transform: vi.fn(),
      beginPath: vi.fn(),
      closePath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn()
    })
  }
}))

// 模拟环境变量
vi.stubGlobal('import.meta', {
  env: {
    VITE_API_BASE_URL: 'http://localhost:8000'
  }
})

// 清理所有定时器
beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.clearAllTimers()
  vi.useRealTimers()
})

// 配置全局属性
config.global.mocks = {
  $t: (key: string) => key,
  $route: {
    params: {},
    query: {},
    path: '/'
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn()
  }
}

// 配置全局指令
config.global.directives = {
  loading: true
}

// 配置全局组件
config.global.stubs = {
  transition: false,
  'el-button': true,
  'el-input': true,
  'el-select': true,
  'el-option': true,
  'el-table': true,
  'el-table-column': true,
  'el-pagination': true,
  'el-tag': true,
  'el-progress': true,
  'el-descriptions': true,
  'el-descriptions-item': true,
  'el-loading': true
}

// 模拟浏览器 API
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = MockResizeObserver
global.IntersectionObserver = MockIntersectionObserver

global.matchMedia = vi.fn().mockReturnValue({
  matches: false,
  addListener: vi.fn(),
  removeListener: vi.fn()
})

// 导出全局实例供测试使用
export { app, pinia } 