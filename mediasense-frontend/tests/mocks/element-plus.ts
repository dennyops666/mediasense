import { vi } from 'vitest'
import { Component, Plugin } from 'vue'

const mockComponent = (name: string): Component => ({
  name,
  template: `<div class="${name}"><slot></slot></div>`
})

export const ElButton = mockComponent('el-button')
export const ElInput = mockComponent('el-input')
export const ElForm = mockComponent('el-form')
export const ElFormItem = mockComponent('el-form-item')
export const ElTable = mockComponent('el-table')
export const ElTableColumn = mockComponent('el-table-column')
export const ElDialog = mockComponent('el-dialog')
export const ElSelect = mockComponent('el-select')
export const ElOption = mockComponent('el-option')
export const ElDatePicker = mockComponent('el-date-picker')
export const ElPagination = mockComponent('el-pagination')
export const ElAlert = mockComponent('el-alert')
export const ElSkeleton = mockComponent('el-skeleton')
export const ElSkeletonItem = mockComponent('el-skeleton-item')
export const ElEmpty = mockComponent('el-empty')
export const ElImage = mockComponent('el-image')

export const ElMessage = {
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
  info: vi.fn()
}

export const ElMessageBox = {
  confirm: vi.fn().mockResolvedValue(true),
  alert: vi.fn().mockResolvedValue(true)
}

export const ElLoading = {
  service: vi.fn(() => ({
    close: vi.fn()
  }))
}

export const vLoading = {
  mounted: vi.fn(),
  updated: vi.fn(),
  unmounted: vi.fn()
}

const ElementPlus: Plugin = {
  install(app) {
    app.component('el-button', ElButton)
    app.component('el-input', ElInput)
    app.component('el-form', ElForm)
    app.component('el-form-item', ElFormItem)
    app.component('el-table', ElTable)
    app.component('el-table-column', ElTableColumn)
    app.component('el-dialog', ElDialog)
    app.component('el-select', ElSelect)
    app.component('el-option', ElOption)
    app.component('el-date-picker', ElDatePicker)
    app.component('el-pagination', ElPagination)
    app.component('el-alert', ElAlert)
    app.component('el-skeleton', ElSkeleton)
    app.component('el-skeleton-item', ElSkeletonItem)
    app.component('el-empty', ElEmpty)
    app.component('el-image', ElImage)

    app.directive('loading', vLoading)
  }
}

export default ElementPlus