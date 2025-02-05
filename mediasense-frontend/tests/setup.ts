import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// 配置全局组件
config.global.plugins = [ElementPlus]

vi.mock('@element-plus/icons-vue', () => ({
  Check: { render: () => null },
  Loading: { render: () => null },
  Search: { render: () => null },
  User: { render: () => null },
  CircleClose: { render: () => null },
  Close: { render: () => null },
  Edit: { render: () => null },
  Delete: { render: () => null },
  Plus: { render: () => null },
  Warning: { render: () => null },
  Success: { render: () => null },
  Info: { render: () => null },
  Error: { render: () => null },
  ArrowDown: { render: () => null },
  Connection: { render: () => null },
  Lock: { render: () => null },
  Message: { render: () => null }
}))

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn().mockResolvedValue({ data: {} }),
      post: vi.fn().mockResolvedValue({ data: {} }),
      put: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() }
      }
    })
  }
}))

// 模拟 Element Plus 的组件和指令
const mockComponent = {
  template: '<div><slot></slot><slot name="header"></slot><slot name="dropdown"></slot></div>',
  props: {
    modelValue: null
  },
  emits: ['update:modelValue', 'click', 'change']
}

const mockDirective = {
  mounted: () => {},
  updated: () => {},
  unmounted: () => {}
}

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual as any,
    ElDescriptions: mockComponent,
    ElDescriptionsItem: mockComponent,
    ElInputNumber: mockComponent,
    ElCollapse: mockComponent,
    ElCollapseItem: mockComponent,
    ElDatePicker: mockComponent,
    ElTable: mockComponent,
    ElTableColumn: mockComponent,
    ElButton: mockComponent,
    ElDialog: mockComponent,
    ElForm: mockComponent,
    ElFormItem: mockComponent,
    ElInput: mockComponent,
    ElSelect: mockComponent,
    ElOption: mockComponent,
    ElSwitch: mockComponent,
    ElTabs: mockComponent,
    ElTabPane: mockComponent,
    ElCard: mockComponent,
    ElMenu: mockComponent,
    ElMenuItem: mockComponent,
    ElDropdown: mockComponent,
    ElDropdownMenu: mockComponent,
    ElDropdownItem: mockComponent,
    ElContainer: mockComponent,
    ElHeader: mockComponent,
    ElMain: mockComponent,
    ElFooter: mockComponent,
    ElLink: mockComponent,
    ElIcon: mockComponent,
    ElMessage: {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn(),
      info: vi.fn()
    },
    vLoading: mockDirective
  }
})

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

// Mock console.error to suppress unnecessary warnings
console.error = vi.fn()

// Mock CSS modules
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.less', () => ({}))
vi.mock('*.sass', () => ({})) 