import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import CrawlerTaskLog from '@/components/crawler/CrawlerTaskLog.vue'
import { ElMessage } from 'element-plus'

const mockLogs = [
  {
    id: 1,
    taskId: 1,
    level: 'INFO',
    message: 'Task started',
    timestamp: '2024-03-20 10:00:00'
  },
  {
    id: 2,
    taskId: 1,
    level: 'ERROR',
    message: 'Task failed',
    timestamp: '2024-03-20 10:01:00'
  }
]

describe('CrawlerTaskLog.vue', () => {
  let wrapper: any
  let store: any

  beforeEach(() => {
    store = createTestingPinia({
      initialState: {
        crawler: {
          logs: mockLogs,
          loading: false,
          error: null
        }
      },
      createSpy: vi.fn
    })

    wrapper = mount(CrawlerTaskLog, {
      props: {
        taskId: 1
      },
      global: {
        plugins: [store],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper.unmount()
  })

  it('应该正确渲染日志列表', () => {
    const rows = wrapper.findAll('[data-test="log-row"]')
    expect(rows).toHaveLength(mockLogs.length)
  })

  it('应该正确显示日志级别标签', () => {
    const tags = wrapper.findAll('[data-test="log-level"]')
    expect(tags).toHaveLength(mockLogs.length)
    expect(tags[0].text()).toBe('INFO')
    expect(tags[1].text()).toBe('ERROR')
  })

  it('应该支持日志过滤', async () => {
    const select = wrapper.find('[data-test="level-filter"]')
    await select.setValue('ERROR')
    
    expect(wrapper.emitted('filter')).toBeTruthy()
    expect(wrapper.emitted('filter')[0]).toEqual(['ERROR'])
  })

  it('应该支持日志搜索', async () => {
    const input = wrapper.find('[data-test="search-input"]')
    await input.setValue('failed')
    
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0]).toEqual(['failed'])
  })

  it('应该支持日志导出', async () => {
    const exportButton = wrapper.find('[data-test="export-button"]')
    await exportButton.trigger('click')
    
    expect(store.exportLogs).toHaveBeenCalledWith(1)
  })

  it('应该显示加载状态', async () => {
    await wrapper.setProps({
      loading: true
    })
    
    const loading = wrapper.find('[data-test="loading"]')
    expect(loading.exists()).toBe(true)
  })

  it('应该显示错误信息', async () => {
    await wrapper.setProps({
      error: 'Failed to fetch logs'
    })
    
    const error = wrapper.find('[data-test="error-message"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('Failed to fetch logs')
  })
}) 