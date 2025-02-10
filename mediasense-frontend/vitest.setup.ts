import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ElementPlus from 'element-plus'
import * as ElementPlusComponents from './tests/unit/mocks/element-plus'
import { afterEach, beforeEach } from 'vitest'

// 创建全局的 Pinia 实例
const pinia = createPinia()

// 清理和重置
beforeEach(() => {
  // 重置 Vue Test Utils 配置
  config.global.plugins = []
  config.global.components = {}
  config.global.directives = {}
  config.global.mocks = {}
  
  // 重新设置 Pinia
  setActivePinia(pinia)
  
  // 全局 mock
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
  
  // Mock Element Plus 消息组件
  vi.mock('element-plus', () => ({
    ElMessage: {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue(true),
      alert: vi.fn().mockResolvedValue(true)
    },
    ElLoading: {
      service: vi.fn().mockReturnValue({
        close: vi.fn()
      })
    }
  }))
})

// 注册 Element Plus 组件和指令
config.global.components = {
  ...ElementPlusComponents
}

// 模拟浏览器 API
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.matchMedia = vi.fn().mockReturnValue({
  matches: false,
  addListener: vi.fn(),
  removeListener: vi.fn()
})

// 清理
afterEach(() => {
  vi.clearAllMocks()
})

