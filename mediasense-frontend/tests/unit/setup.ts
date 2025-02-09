import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 设置全局的 vi
global.vi = vi

// 配置 Vue Test Utils
config.global.plugins = [ElementPlus]

// 配置全局 stubs
config.global.stubs = {
  transition: false,
  'el-button': {
    template: '<button><slot/></button>',
    props: ['type', 'size', 'loading', 'disabled']
  },
  'el-table': {
    template: '<div><slot/></div>',
    props: ['data']
  },
  'el-table-column': {
    template: '<div><slot :row="$parent.data[0]"/></div>',
    props: ['prop', 'label']
  },
  'el-tag': {
    template: '<span><slot/></span>',
    props: ['type']
  },
  'el-pagination': {
    template: '<div><slot/></div>',
    props: ['total', 'page-size', 'current-page'],
    emits: ['update:current-page', 'update:page-size', 'size-change', 'current-change']
  },
  'el-radio': {
    template: '<input type="radio"><slot/></input>',
    props: ['modelValue', 'label'],
    emits: ['update:modelValue']
  },
  'el-radio-group': {
    template: '<div><slot/></div>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-input': {
    template: '<input type="text" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)"/>',
    props: ['modelValue'],
    emits: ['update:modelValue', 'input', 'change']
  },
  'el-input-number': {
    template: '<input type="number" :value="modelValue" @input="$emit(\'update:modelValue\', Number($event.target.value))"/>',
    props: ['modelValue', 'min', 'max', 'step'],
    emits: ['update:modelValue', 'change']
  },
  'el-date-picker': {
    template: '<input type="date"/>',
    props: ['modelValue', 'type', 'placeholder'],
    emits: ['update:modelValue']
  },
  'el-select': {
    template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot/></select>',
    props: ['modelValue'],
    emits: ['update:modelValue', 'change']
  },
  'el-option': {
    template: '<option :value="value"><slot/></option>',
    props: ['value', 'label']
  },
  'el-dialog': {
    template: '<div v-if="modelValue"><slot/><slot name="footer"/></div>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-collapse': {
    template: '<div><slot/></div>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-collapse-item': {
    template: '<div><slot/></div>',
    props: ['name', 'title']
  },
  'el-card': {
    template: '<div><slot name="header"/><slot/></div>'
  },
  'el-form': {
    template: '<form @submit.prevent="$emit(\'submit\', $event)"><slot/></form>',
    props: ['model', 'rules']
  },
  'el-form-item': {
    template: '<div><slot/></div>',
    props: ['label', 'prop']
  }
}

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  config.global.components[key] = component
}

// Mock Canvas API
const mockCanvasContext = {
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 1,
  font: '',
  textAlign: 'start',
  textBaseline: 'alphabetic',
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  stroke: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  fillText: vi.fn(),
  save: vi.fn(),
  restore: vi.fn()
}

// @ts-ignore
window.HTMLCanvasElement.prototype.getContext = function() {
  return mockCanvasContext
}

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString()
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

window.ResizeObserver = MockResizeObserver

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

window.IntersectionObserver = MockIntersectionObserver

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual as any,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

// Mock ECharts
vi.mock('echarts/core', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  })),
  use: vi.fn(),
}))

// Mock CSS modules
vi.mock('*.module.css', () => ({}))
vi.mock('*.module.scss', () => ({}))

// Mock Axios
const mockAxiosInstance = {
  get: vi.fn(() => Promise.resolve({ data: {} })),
  post: vi.fn(() => Promise.resolve({ data: {} })),
  put: vi.fn(() => Promise.resolve({ data: {} })),
  delete: vi.fn(() => Promise.resolve({ data: {} })),
  patch: vi.fn(() => Promise.resolve({ data: {} })),
  request: vi.fn(() => Promise.resolve({ data: {} })),
  interceptors: {
    request: {
      handlers: [],
      use(onFulfilled, onRejected) {
        const id = this.handlers.length
        this.handlers.push({ onFulfilled, onRejected })
        return id
      },
      eject(id) {
        if (id >= 0 && id < this.handlers.length) {
          this.handlers[id] = null
        }
      }
    },
    response: {
      handlers: [],
      use(onFulfilled, onRejected) {
        const id = this.handlers.length
        this.handlers.push({ onFulfilled, onRejected })
        return id
      },
      eject(id) {
        if (id >= 0 && id < this.handlers.length) {
          this.handlers[id] = null
        }
      }
    }
  }
}

vi.mock('axios', () => ({
  default: {
    create: () => mockAxiosInstance,
    ...mockAxiosInstance
  }
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class ResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

window.ResizeObserver = ResizeObserver

// Mock IntersectionObserver
class IntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

window.IntersectionObserver = IntersectionObserver

// Mock ECharts
vi.mock('echarts/core', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    getOption: vi.fn(() => ({
      xAxis: [{ data: [] }],
      series: [{ data: [] }]
    }))
  })),
  use: vi.fn()
}))

// 使用假计时器
vi.useFakeTimers()

// Mock CSS modules
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.sass', () => ({}))

// 导出模拟的消息服务以供测试使用
export { ElMessage, ElMessageBox } 