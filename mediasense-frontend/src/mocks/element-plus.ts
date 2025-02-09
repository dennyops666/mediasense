import { Component, Plugin } from 'vue'
import { defineComponent } from 'vue'

// 创建基础组件 mock
const createBaseMock = (name: string) => defineComponent({
  name,
  template: `<div class="${name}"><slot></slot></div>`
})

// 创建表单组件 mock
const createFormMock = (name: string) => defineComponent({
  name,
  props: {
    model: Object,
    rules: Object,
    inline: Boolean,
    labelPosition: String,
    labelWidth: [String, Number],
    labelSuffix: String,
    hideRequiredAsterisk: Boolean,
    showMessage: Boolean,
    inlineMessage: Boolean,
    statusIcon: Boolean,
    validateOnRuleChange: Boolean,
    size: String,
    disabled: Boolean
  },
  emits: ['validate'],
  template: `<form class="${name}"><slot></slot></form>`
})

// 创建输入组件 mock
const createInputMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: [String, Number],
    type: String,
    size: String,
    placeholder: String,
    clearable: Boolean,
    disabled: Boolean,
    readonly: Boolean,
    maxlength: Number,
    minlength: Number,
    showPassword: Boolean,
    showWordLimit: Boolean
  },
  emits: ['update:modelValue', 'input', 'change', 'focus', 'blur', 'clear'],
  template: `<input class="${name}" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)">`
})

// 创建按钮组件 mock
const createButtonMock = (name: string) => defineComponent({
  name,
  props: {
    type: String,
    size: String,
    icon: String,
    loading: Boolean,
    disabled: Boolean,
    plain: Boolean,
    round: Boolean,
    circle: Boolean
  },
  template: `<button class="${name}"><slot></slot></button>`
})

// 创建表格组件 mock
const createTableMock = (name: string) => defineComponent({
  name,
  props: {
    data: Array,
    height: [String, Number],
    maxHeight: [String, Number],
    stripe: Boolean,
    border: Boolean,
    size: String,
    fit: Boolean,
    showHeader: Boolean,
    highlightCurrentRow: Boolean,
    rowClassName: [String, Function],
    rowStyle: [Object, Function],
    cellClassName: [String, Function],
    cellStyle: [Object, Function],
    headerRowClassName: [String, Function],
    headerRowStyle: [Object, Function],
    headerCellClassName: [String, Function],
    headerCellStyle: [Object, Function]
  },
  template: `<table class="${name}"><slot></slot></table>`
})

// 创建对话框组件 mock
const createDialogMock = (name: string) => defineComponent({
  name,
  props: {
    modelValue: Boolean,
    title: String,
    width: String,
    fullscreen: Boolean,
    top: String,
    modal: Boolean,
    appendToBody: Boolean,
    lockScroll: Boolean,
    customClass: String,
    closeOnClickModal: Boolean,
    closeOnPressEscape: Boolean,
    showClose: Boolean,
    beforeClose: Function,
    center: Boolean,
    destroyOnClose: Boolean
  },
  emits: ['update:modelValue', 'open', 'opened', 'close', 'closed'],
  template: `<div v-if="modelValue" class="${name}"><slot></slot></div>`
})

// 创建消息组件 mock
const ElMessage = {
  success: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
  error: vi.fn()
}

// 创建消息框组件 mock
const ElMessageBox = {
  alert: vi.fn().mockResolvedValue({}),
  confirm: vi.fn().mockResolvedValue({}),
  prompt: vi.fn().mockResolvedValue({ value: 'mock input' }),
  close: vi.fn()
}

// 创建加载组件 mock
const ElLoading = {
  service: vi.fn().mockReturnValue({
    close: vi.fn()
  })
}

// 创建 v-loading 指令
const vLoading = {
  mounted(el: any, binding: any) {
    el.instance = ElLoading.service({
      target: el,
      fullscreen: binding.modifiers.fullscreen
    })
  },
  updated(el: any, binding: any) {
    if (binding.value !== binding.oldValue) {
      if (binding.value) {
        el.instance = ElLoading.service({
          target: el,
          fullscreen: binding.modifiers.fullscreen
        })
      } else {
        el.instance?.close()
      }
    }
  },
  unmounted(el: any) {
    el.instance?.close()
  }
}

// 创建组件实例
export const ElForm = createFormMock('el-form')
export const ElFormItem = createBaseMock('el-form-item')
export const ElInput = createInputMock('el-input')
export const ElButton = createButtonMock('el-button')
export const ElTable = createTableMock('el-table')
export const ElTableColumn = createBaseMock('el-table-column')
export const ElDialog = createDialogMock('el-dialog')
export const ElSelect = createBaseMock('el-select')
export const ElOption = createBaseMock('el-option')
export const ElDatePicker = createBaseMock('el-date-picker')
export const ElTimePicker = createBaseMock('el-time-picker')
export const ElPagination = createBaseMock('el-pagination')
export const ElPopover = createBaseMock('el-popover')
export const ElTooltip = createBaseMock('el-tooltip')
export const ElDropdown = createBaseMock('el-dropdown')
export const ElDropdownMenu = createBaseMock('el-dropdown-menu')
export const ElDropdownItem = createBaseMock('el-dropdown-item')
export const ElMenu = createBaseMock('el-menu')
export const ElMenuItem = createBaseMock('el-menu-item')
export const ElSubmenu = createBaseMock('el-submenu')
export const ElBreadcrumb = createBaseMock('el-breadcrumb')
export const ElBreadcrumbItem = createBaseMock('el-breadcrumb-item')
export const ElTabs = createBaseMock('el-tabs')
export const ElTabPane = createBaseMock('el-tab-pane')
export const ElAlert = createBaseMock('el-alert')
export const ElTag = createBaseMock('el-tag')
export const ElTree = createBaseMock('el-tree')
export const ElUpload = createBaseMock('el-upload')
export const ElProgress = createBaseMock('el-progress')
export const ElSkeleton = createBaseMock('el-skeleton')
export const ElSkeletonItem = createBaseMock('el-skeleton-item')
export const ElImage = createBaseMock('el-image')
export const ElDescriptions = createBaseMock('el-descriptions')
export const ElDescriptionsItem = createBaseMock('el-descriptions-item')
export const ElCollapse = createBaseMock('el-collapse')
export const ElCollapseItem = createBaseMock('el-collapse-item')
export const ElLink = createBaseMock('el-link')
export const ElEmpty = createBaseMock('el-empty')

// 导出所有组件和服务
export {
  ElMessage,
  ElMessageBox,
  ElLoading,
  vLoading
}

// 创建插件对象
const ElementPlus: Plugin = {
  install(app) {
    // 注册全局组件
    const components = {
      ElForm,
      ElFormItem,
      ElInput,
      ElButton,
      ElTable,
      ElTableColumn,
      ElDialog,
      ElSelect,
      ElOption,
      ElDatePicker,
      ElTimePicker,
      ElPagination,
      ElPopover,
      ElTooltip,
      ElDropdown,
      ElDropdownMenu,
      ElDropdownItem,
      ElMenu,
      ElMenuItem,
      ElSubmenu,
      ElBreadcrumb,
      ElBreadcrumbItem,
      ElTabs,
      ElTabPane,
      ElAlert,
      ElTag,
      ElTree,
      ElUpload,
      ElProgress,
      ElSkeleton,
      ElSkeletonItem,
      ElImage,
      ElDescriptions,
      ElDescriptionsItem,
      ElCollapse,
      ElCollapseItem,
      ElLink,
      ElEmpty
    }

    Object.entries(components).forEach(([name, component]) => {
      app.component(name, component)
    })

    // 注册全局指令
    app.directive('loading', vLoading)

    // 注册全局属性
    app.config.globalProperties.$message = ElMessage
    app.config.globalProperties.$msgbox = ElMessageBox
    app.config.globalProperties.$alert = ElMessageBox.alert
    app.config.globalProperties.$confirm = ElMessageBox.confirm
    app.config.globalProperties.$prompt = ElMessageBox.prompt
    app.config.globalProperties.$loading = ElLoading.service
  }
}

// 默认导出插件
export default ElementPlus 