import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick } from 'vue'
import CrawlerDataList from '@/components/crawler/CrawlerDataList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import type { MessageBoxData } from 'element-plus'
import type { CrawlerData } from '@/types/crawler'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('CrawlerDataList.vue', () => {
  let wrapper
  let store

  const mockData: CrawlerData[] = [
    {
      id: '1',
      title: '测试数据1',
      url: 'http://example.com/1',
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: '2',
      title: '测试数据2',
      url: 'http://example.com/2',
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()

    wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                data: [],
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-input': true,
          'el-dialog': true,
          'el-pagination': true
        }
      }
    })

    store = useCrawlerStore()
    store.fetchData.mockResolvedValue({
      items: mockData,
      total: mockData.length
    })
  })

  afterEach(() => {
    wrapper.unmount()
    vi.clearAllMocks()
  })

  it('显示数据列表', async () => {
    await wrapper.vm.$nextTick()
    expect(store.fetchData).toHaveBeenCalledWith({
      taskId: '1',
      page: 1,
      pageSize: 10
    })
  })

  it('处理数据搜索', async () => {
    const searchInput = wrapper.find('[data-test="search-input"]')
    await searchInput.setValue('测试')
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredData.length).toBe(2)
  })

  it('查看数据详情', async () => {
    store.data = mockData
    await wrapper.vm.$nextTick()
    await wrapper.vm.handleView(mockData[0])
    expect(wrapper.vm.dialogVisible).toBe(true)
    expect(wrapper.vm.currentData).toEqual(mockData[0])
  })

  it('删除数据', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as MessageBoxData)
    store.deleteData.mockResolvedValue()
    await wrapper.vm.handleDelete(mockData[0])
    expect(store.deleteData).toHaveBeenCalledWith('1')
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })

  it('导出数据', async () => {
    store.exportData.mockResolvedValue()
    await wrapper.vm.handleExport()
    expect(store.exportData).toHaveBeenCalledWith({
      taskId: '1'
    })
    expect(ElMessage.success).toHaveBeenCalledWith('导出成功')
  })

  it('处理错误状态', async () => {
    store.fetchData.mockRejectedValue(new Error('获取数据失败'))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-message"]').exists()).toBe(true)
  })
}) 