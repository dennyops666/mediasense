import { vi } from 'vitest'
import { defineComponent, h } from 'vue'

// 创建基础组件 mock
const createBaseMock = (name: string) => defineComponent({
  name,
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建表单组件 mock
const createFormMock = (name: string) => defineComponent({
  name,
  props: {
    model: Object,
    rules: Object,
    labelWidth: String,
    inline: Boolean
  },
  render() {
    return h('form', { class: name }, this.$slots.default?.())
  }
})

// 创建输入组件 mock
const createInputMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [String, Number],
    placeholder: String,
    'data-test': String
  },
  emits: ['update:modelValue', 'input'],
  render() {
    return h('input', {
      class: 'el-input',
      value: this.modelValue,
      placeholder: this.placeholder,
      'data-test': this['data-test'],
      onInput: (e: Event) => {
        const target = e.target as HTMLInputElement
        this.$emit('update:modelValue', target.value)
        this.$emit('input', target.value)
      }
    })
  }
})

// 创建按钮组件 mock
const createButtonMock = (name: string) => defineComponent({
  name,
  props: {
    type: String,
    size: String,
    disabled: Boolean,
    'data-test': String
  },
  emits: ['click'],
  render() {
    return h('button', {
      class: ['el-button', `el-button--${this.type}`],
      disabled: this.disabled,
      'data-test': this['data-test'],
      onClick: (e: Event) => this.$emit('click', e)
    }, this.$slots.default?.())
  }
})

// 创建表格组件 mock
const createTableMock = (name: string) => defineComponent({
  name,
  props: {
    data: {
      type: Array,
      default: () => []
    },
    loading: Boolean
  },
  render() {
    return h('div', { class: 'el-table' }, [
      this.$slots.default?.({
        row: {},
        $index: 0
      })
    ])
  }
})

// 创建分页组件 mock
const createPaginationMock = (name: string) => defineComponent({
  name,
  props: {
    total: Number,
    currentPage: Number,
    pageSize: Number
  },
  emits: ['current-change', 'size-change'],
  render() {
    return h('div', { class: name })
  }
})

// 创建对话框组件 mock
const createDialogMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: Boolean,
    title: String,
    width: String
  },
  emits: ['update:modelValue'],
  render() {
    return this.modelValue ? h('div', { class: name }, this.$slots.default?.()) : null
  }
})

// 创建标签页组件 mock
const createTabsMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: String,
    type: String
  },
  emits: ['update:modelValue'],
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建标签面板组件 mock
const createTabPaneMock = (name: string) => defineComponent({
  name,
  props: {
    label: String,
    name: String
  },
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建卡片组件 mock
const createCardMock = (name: string) => defineComponent({
  name,
  props: {
    shadow: String,
    bodyStyle: Object
  },
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建进度条组件 mock
const createProgressMock = (name: string) => defineComponent({
  name,
  props: {
    percentage: Number,
    type: String,
    strokeWidth: Number,
    textInside: Boolean,
    status: String
  },
  render() {
    return h('div', { class: name }, [
      h('div', { class: `${name}-bar`, style: { width: `${this.percentage}%` } }),
      h('span', { class: `${name}-text` }, `${this.percentage}%`)
    ])
  }
})

// 创建警告组件 mock
const createAlertMock = (name: string) => defineComponent({
  name,
  props: {
    title: String,
    type: String,
    description: String,
    closable: Boolean,
    showIcon: Boolean
  },
  render() {
    return h('div', { class: name }, [
      this.title && h('span', { class: `${name}-title` }, this.title),
      this.description && h('p', { class: `${name}-description` }, this.description)
    ])
  }
})

// 创建单选组件 mock
const createRadioMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [String, Number, Boolean],
    label: [String, Number, Boolean],
    disabled: Boolean
  },
  emits: ['update:modelValue'],
  render() {
    return h('input', {
      type: 'radio',
      class: name,
      checked: this.modelValue === this.label,
      onChange: () => this.$emit('update:modelValue', this.label)
    })
  }
})

// 创建单选组组件 mock
const createRadioGroupMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [String, Number, Boolean],
    disabled: Boolean
  },
  emits: ['update:modelValue'],
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建行组件 mock
const createRowMock = (name: string) => defineComponent({
  name,
  props: {
    gutter: Number,
    justify: String,
    align: String
  },
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建列组件 mock
const createColMock = (name: string) => defineComponent({
  name,
  props: {
    span: Number,
    offset: Number,
    push: Number,
    pull: Number
  },
  render() {
    return h('div', { class: name }, this.$slots.default?.())
  }
})

// 创建日期选择器组件 mock
const createDatePickerMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [Date, Array, String],
    type: String,
    placeholder: String,
    format: String,
    valueFormat: String
  },
  emits: ['update:modelValue'],
  render() {
    return h('input', {
      class: name,
      value: this.modelValue,
      onChange: (e: Event) => this.$emit('update:modelValue', (e.target as HTMLInputElement).value)
    })
  }
})

// 创建选择器组件 mock
const createSelectMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [String, Number, Array],
    placeholder: String,
    'data-test': String
  },
  emits: ['update:modelValue', 'change'],
  render() {
    return h('select', {
      class: 'el-select',
      value: this.modelValue,
      'data-test': this['data-test'],
      onChange: (e: Event) => {
        const target = e.target as HTMLSelectElement
        this.$emit('update:modelValue', target.value)
        this.$emit('change', target.value)
      }
    }, this.$slots.default?.())
  }
})

// 创建选项组件 mock
const createOptionMock = (name: string) => defineComponent({
  name,
  props: {
    value: [String, Number, Boolean],
    label: [String, Number],
    disabled: Boolean
  },
  render() {
    return h('option', {
      class: name,
      value: this.value
    }, this.label || this.value)
  }
})

// 创建开关组件 mock
const createSwitchMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: Boolean,
    disabled: Boolean,
    activeText: String,
    inactiveText: String
  },
  emits: ['update:modelValue'],
  render() {
    return h('input', {
      type: 'checkbox',
      class: name,
      checked: this.modelValue,
      onChange: () => this.$emit('update:modelValue', !this.modelValue)
    })
  }
})

// 创建空状态组件 mock
const createEmptyMock = (name: string) => defineComponent({
  name,
  props: {
    description: String,
    image: String
  },
  render() {
    return h('div', { class: name }, [
      this.image && h('img', { src: this.image }),
      this.description && h('p', {}, this.description)
    ])
  }
})

// 创建骨架屏组件 mock
const createSkeletonMock = (name: string) => defineComponent({
  name,
  props: {
    rows: Number,
    animated: Boolean,
    loading: Boolean
  },
  render() {
    return h('div', { class: name }, Array(this.rows || 1).fill(0).map(() => 
      h('div', { class: `${name}-item ${this.animated ? 'animated' : ''}` })
    ))
  }
})

// 创建表格列组件 mock
const createTableColumnMock = (name: string) => defineComponent({
  name,
  props: {
    prop: String,
    label: String,
    width: [String, Number],
    type: String
  },
  render() {
    return h('div', { class: 'el-table-column' }, [
      this.$slots.default?.({
        row: {},
        $index: 0
      })
    ])
  }
})

// 导出所有组件
export const ElButton = createButtonMock('el-button')
export const ElInput = createInputMock('el-input')
export const ElForm = createFormMock('el-form')
export const ElFormItem = createBaseMock('el-form-item')
export const ElTable = createTableMock('el-table')
export const ElTableColumn = createTableColumnMock('el-table-column')
export const ElPagination = createPaginationMock('el-pagination')
export const ElDialog = createDialogMock('el-dialog')
export const ElTabs = createTabsMock('el-tabs')
export const ElTabPane = createTabPaneMock('el-tab-pane')
export const ElCard = createCardMock('el-card')
export const ElProgress = createProgressMock('el-progress')
export const ElAlert = createAlertMock('el-alert')
export const ElRadio = createRadioMock('el-radio')
export const ElRadioGroup = createRadioGroupMock('el-radio-group')
export const ElRow = createRowMock('el-row')
export const ElCol = createColMock('el-col')
export const ElDatePicker = createDatePickerMock('el-date-picker')
export const ElSelect = createSelectMock('el-select')
export const ElOption = createOptionMock('el-option')
export const ElSwitch = createSwitchMock('el-switch')
export const ElEmpty = createEmptyMock('el-empty')
export const ElSkeleton = createSkeletonMock('el-skeleton')
export const ElSkeletonItem = createBaseMock('el-skeleton-item')

export default {
  install: (app: any) => {
    const components = {
      ElInput,
      ElButton,
      ElCard,
      ElProgress,
      ElAlert,
      ElTable,
      ElTableColumn,
      ElPagination,
      ElDialog,
      ElTabs,
      ElTabPane,
      ElForm,
      ElFormItem,
      ElRadio,
      ElRadioGroup,
      ElRow,
      ElCol,
      ElDatePicker,
      ElSelect,
      ElOption,
      ElSwitch,
      ElEmpty,
      ElSkeleton,
      ElSkeletonItem
    }
    
    Object.entries(components).forEach(([name, component]) => {
      app.component(name, component)
    })
  }
}

// Mock ElMessage
export const ElMessage = {
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
  info: vi.fn()
}

// Mock ElMessageBox
export const ElMessageBox = {
  confirm: vi.fn(),
  alert: vi.fn(),
  prompt: vi.fn()
}

// Mock ElLoading
export const ElLoading = {
  service: vi.fn(() => ({
    close: vi.fn()
  }))
} 