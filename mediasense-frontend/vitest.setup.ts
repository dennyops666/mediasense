import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import { h } from 'vue'

// 配置Vue Test Utils
config.global.stubs = {
  'el-icon': true,
  'el-button-group': true,
  'el-link': true
}

// 模拟CSS模块
vi.mock('*.css', () => ({
  default: {}
}))

// 模拟Element Plus图标
vi.mock('@element-plus/icons-vue', () => ({
  Check: { render: () => null },
  Loading: { render: () => null },
  Search: { render: () => null },
  User: { render: () => null },
  CircleClose: { render: () => null },
  ArrowDown: { render: () => null },
  Lock: { render: () => null },
  Message: { render: () => null },
  Connection: { render: () => null },
  Close: { render: () => null }
}))

// 模拟Element Plus
vi.mock('element-plus', () => {
  const loadingDirective = {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
  
  const createComponent = (name: string, options = {}) => {
    const defaultProps = {
      modelValue: null,
      ...options.props
    }

    const defaultEmits = ['update:modelValue', 'click', 'change', 'input', ...(options.emits || [])]

    return {
      name,
      inheritAttrs: false,
      render() {
        const slots = {}
        const attrs = { ...this.$attrs }
        
        if (this.$slots.default) {
          if (typeof this.$slots.default === 'function') {
            const defaultSlot = this.$slots.default({
              row: attrs.data?.[0] || {},
              $index: 0,
              ...attrs
            })
            slots.default = () => defaultSlot
          } else {
            slots.default = () => this.$slots.default
          }
        }

        // 移除特殊属性，避免警告
        delete attrs.data

        const tag = name.toLowerCase()
        const className = [tag, attrs.class]
        const style = attrs.style || {}

        return h('div', {
          class: className,
          style,
          'data-test': tag,
          ...attrs,
          onClick: (e) => {
            this.$emit('click', e)
            if (attrs.onClick) {
              attrs.onClick(e)
            }
          },
          onInput: (e) => {
            const value = e.target.value
            this.$emit('update:modelValue', value)
            this.$emit('input', value)
            if (attrs.onInput) {
              attrs.onInput(e)
            }
          },
          onChange: (e) => {
            const value = e.target.value
            this.$emit('change', value)
            if (attrs.onChange) {
              attrs.onChange(e)
            }
          }
        }, slots)
      },
      props: defaultProps,
      emits: defaultEmits,
      methods: {
        ...(options.methods || {}),
        focus: vi.fn(),
        blur: vi.fn(),
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }
    }
  }
  
  return {
    default: {
      install: vi.fn(),
      directive: (name: string) => {
        if (name === 'loading') {
          return loadingDirective
        }
      }
    },
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
      service: vi.fn(() => ({
        close: vi.fn()
      })),
      directive: loadingDirective
    },
    ElTable: createComponent('ElTable', {
      props: {
        data: { type: Array, default: () => [] }
      }
    }),
    ElTableColumn: createComponent('ElTableColumn', {
      props: {
        prop: String,
        label: String
      }
    }),
    ElButton: createComponent('ElButton', {
      props: {
        type: String,
        size: String
      }
    }),
    ElDialog: createComponent('ElDialog', {
      props: {
        modelValue: Boolean,
        title: String
      },
      emits: ['update:modelValue', 'close']
    }),
    ElForm: createComponent('ElForm', {
      props: {
        model: Object,
        rules: Object
      },
      methods: {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }
    }),
    ElFormItem: createComponent('ElFormItem', {
      props: {
        label: String,
        prop: String
      }
    }),
    ElInput: createComponent('ElInput', {
      props: {
        modelValue: [String, Number],
        type: String,
        placeholder: String
      }
    }),
    ElInputNumber: createComponent('ElInputNumber', {
      props: {
        modelValue: Number,
        min: Number,
        max: Number
      }
    }),
    ElSelect: createComponent('ElSelect', {
      props: {
        modelValue: null,
        placeholder: String
      }
    }),
    ElOption: createComponent('ElOption', {
      props: {
        label: String,
        value: null
      }
    }),
    ElSwitch: createComponent('ElSwitch', {
      props: {
        modelValue: Boolean
      }
    }),
    ElTabs: createComponent('ElTabs', {
      props: {
        modelValue: String
      },
      emits: ['tab-change']
    }),
    ElTabPane: createComponent('ElTabPane', {
      props: {
        label: String,
        name: String
      }
    }),
    ElCard: createComponent('ElCard'),
    ElTag: createComponent('ElTag'),
    ElAlert: createComponent('ElAlert', {
      props: {
        type: String,
        title: String,
        description: String
      }
    }),
    ElDescriptions: createComponent('ElDescriptions', {
      props: {
        column: Number,
        border: Boolean
      }
    }),
    ElDescriptionsItem: createComponent('ElDescriptionsItem', {
      props: {
        label: String,
        span: Number
      }
    }),
    ElDatePicker: createComponent('ElDatePicker', {
      props: {
        modelValue: [String, Date, Array],
        type: String,
        rangeSeparator: String,
        startPlaceholder: String,
        endPlaceholder: String,
        shortcuts: Array
      }
    }),
    ElCollapse: createComponent('ElCollapse', {
      props: {
        modelValue: [String, Array]
      }
    }),
    ElCollapseItem: createComponent('ElCollapseItem', {
      props: {
        title: String,
        name: [String, Number]
      }
    })
  }
})

// 配置全局变量
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

// 配置ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {
    this.callback = callback
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

// 配置IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
} 