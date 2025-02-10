import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import CrawlerTaskLog from '@/components/crawler/CrawlerTaskLog.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage } from 'element-plus'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('CrawlerTaskLog.vue', () => {
  let wrapper
  let store

  const mockLogs = [
    {
      id: '1',
      taskId: '1',
      level: 'INFO',
      message: '开始爬取',
      timestamp: '2024-03-20 10:00:00'
    },
    {
      id: '2',
      taskId: '1',
      level: 'ERROR',
      message: '连接失败',
      timestamp: '2024-03-20 10:01:00'
    }
  ]

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          taskLogs: mockLogs,
          loading: false,
          error: null
        }
      }
    })

    store = useCrawlerStore(pinia)
    store.fetchTaskLogs = vi.fn().mockResolvedValue({ items: mockLogs, total: 2 })
    store.exportTaskLogs = vi.fn().mockResolvedValue()

    wrapper = mount(CrawlerTaskLog, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-table': {
            template: `
              <div class="el-table" :loading="loading">
                <slot name="empty" v-if="!data.length"></slot>
                <template v-else>
                  <div v-for="item in data" :key="item.id" data-test="log-row">
                    <slot :row="item"></slot>
                  </div>
                </template>
              </div>
            `,
            props: ['data', 'loading']
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot :row="row"></slot></div>',
            props: ['prop', 'label', 'row']
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type" data-test="log-level"><slot/></span>',
            props: ['type']
          },
          'el-button': {
            template: '<button :type="type" @click="$emit(\'click\')"><slot/></button>',
            props: ['type']
          },
          'el-input': true,
          'el-select': true,
          'el-option': true
        }
      }
    })

    await nextTick()
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
    await wrapper.vm.handleLevelChange('ERROR')
    expect(store.fetchTaskLogs).toHaveBeenCalledWith({
      taskId: '1',
      level: 'ERROR',
      page: 1,
      pageSize: 10
    })
  })

  it('应该支持日志搜索', async () => {
    await wrapper.vm.handleSearch('error')
    expect(store.fetchTaskLogs).toHaveBeenCalledWith({
      taskId: '1',
      keyword: 'error',
      page: 1,
      pageSize: 10
    })
  })

  it('应该支持日志导出', async () => {
    await wrapper.vm.handleExport()
    expect(store.exportTaskLogs).toHaveBeenCalledWith('1')
    expect(ElMessage.success).toHaveBeenCalledWith('导出成功')
  })

  it('应该显示加载状态', async () => {
    store.loading = true
    await nextTick()
    
    const loading = wrapper.find('[data-test="loading"]')
    expect(loading.exists()).toBe(true)
  })

  it('应该显示错误信息', async () => {
    store.error = 'Failed to fetch logs'
    await nextTick()
    
    const error = wrapper.find('[data-test="error-message"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toBe('Failed to fetch logs')
  })
}) 