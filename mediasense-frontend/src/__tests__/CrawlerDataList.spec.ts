import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import CrawlerDataList from '@/components/crawler/CrawlerDataList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerData } from '@/types/crawler'

const mockData: CrawlerData[] = [
  {
    id: '1',
    title: '测试新闻标题1',
    url: 'http://example.com/news/1',
    content: '测试内容1',
    publishTime: '2024-01-01 12:00:00',
    source: '测试来源1',
    taskId: '1'
  },
  {
    id: '2',
    title: '测试新闻标题2',
    url: 'http://example.com/news/2',
    content: '测试内容2',
    publishTime: '2024-01-02 12:00:00',
    source: '测试来源2',
    taskId: '1'
  }
]

describe('CrawlerDataList 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确显示数据列表', async () => {
    const wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                crawlerData: mockData
              }
            }
          })
        ]
      }
    })

    const store = useCrawlerStore()
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    expect(wrapper.text()).toContain('测试新闻标题1')
    expect(wrapper.text()).toContain('测试新闻标题2')
  })

  it('应该能搜索数据', async () => {
    const wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                crawlerData: mockData
              }
            }
          })
        ]
      }
    })

    const searchInput = wrapper.find('[data-test="search-input"]')
    await searchInput.setValue('标题1')
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.text()).toContain('测试新闻标题1')
    expect(wrapper.text()).not.toContain('测试新闻标题2')
  })

  it('应该能导出数据', async () => {
    const wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                crawlerData: mockData
              }
            }
          })
        ]
      }
    })

    const exportButton = wrapper.find('[data-test="export-button"]')
    await exportButton.trigger('click')

    expect(ElMessage.success).toHaveBeenCalledWith('数据导出成功')
  })

  it('应该能删除数据', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm')
    
    const wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                crawlerData: mockData
              }
            }
          })
        ]
      }
    })

    const deleteButton = wrapper.find('[data-test="delete-button"]')
    await deleteButton.trigger('click')

    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })
}) 