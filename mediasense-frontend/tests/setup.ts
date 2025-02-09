import { config } from '@vue/test-utils'
import { createRouter, createWebHistory, Router } from 'vue-router'
import { createPinia } from 'pinia'
import ElementPlus from './mocks/element-plus'
import { routes } from '@/router'
import axios from 'axios'
import * as echarts from 'echarts'
import { vi } from 'vitest'

// Mock axios
vi.mock('axios')

// Mock echarts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 配置全局组件
config.global.plugins = [
  ElementPlus,
  router,
  createPinia()
]

// 配置全局属性
config.global.mocks = {
  $route: {
    params: {},
    query: {},
    path: '/'
  },
  $router: router
}

// 配置全局 stubs
config.global.stubs = {
  transition: false,
  'router-view': true,
  'router-link': true
}

// Mock ResizeObserver
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock matchMedia
window.matchMedia = vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn()
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock canvas
HTMLCanvasElement.prototype.getContext = vi.fn()

// 导出配置
export { router }