import { Component, Plugin } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'

// ... existing code ...

// 创建插件对象
const ElementPlus: Plugin = {
  install(app) {
    // 注册全局组件
    app.component('ElButton', createButtonMock())
    app.component('ElInput', createInputMock())
    app.component('ElForm', createFormMock())
    app.component('ElFormItem', createFormItemMock())
    app.component('ElSelect', createSelectMock())
    app.component('ElOption', createOptionMock())
    app.component('ElDatePicker', createDatePickerMock())
    app.component('ElTable', createTableMock())
    app.component('ElTableColumn', createTableColumnMock())
    app.component('ElPagination', createPaginationMock())
    app.component('ElDialog', createDialogMock())
    app.component('ElSkeleton', createSkeletonMock())
    app.component('ElSkeletonItem', createSkeletonItemMock())
    app.component('ElImage', createImageMock())
    app.component('ElDescriptions', createDescriptionsMock())
    app.component('ElCollapse', createCollapseMock())
    app.component('ElLink', createLinkMock())
    app.component('ElAlert', createAlertMock())
    app.component('ElEmpty', createEmptyMock())

    // 注册全局指令
    app.directive('loading', vLoading)

    // 注册全局属性
    app.config.globalProperties.$message = ElMessage
    app.config.globalProperties.$msgbox = ElMessageBox
    app.config.globalProperties.$loading = ElLoading.service
  }
}

// 导出插件作为默认导出
export default ElementPlus

// 导出单个组件和指令
export {
  ElButton,
  ElInput,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElDatePicker,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElDialog,
  ElSkeleton,
  ElSkeletonItem,
  ElImage,
  ElDescriptions,
  ElCollapse,
  ElLink,
  ElAlert,
  ElEmpty,
  vLoading,
  ElMessage,
  ElMessageBox,
  ElLoading
} 