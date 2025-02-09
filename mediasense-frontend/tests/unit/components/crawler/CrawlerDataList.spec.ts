import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import { nextTick } from 'vue'
import CrawlerDataList from '@/components/crawler/CrawlerDataList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue(true)
  }
}))

describe('CrawlerDataList.vue', () => {
  let wrapper
  let store

  const mockData = [
    {
      id: '1',
      taskId: '1',
      url: 'https://example.com/1',
      title: 'Example 1',
      content: 'Content 1',
      createdAt: '2024-03-20 10:00:00'
    },
    {
      id: '2',
      taskId: '1',
      url: 'https://example.com/2',
      title: 'Example 2',
      content: 'Content 2',
      createdAt: '2024-03-20 11:00:00'
    }
  ]

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          data: mockData,
          loading: false,
          error: null
        }
      }
    })

    store = useCrawlerStore(pinia)
    store.fetchData = vi.fn().mockResolvedValue(mockData)
    store.deleteData = vi.fn().mockResolvedValue()
    store.exportData = vi.fn().mockResolvedValue()

    wrapper = mount(CrawlerDataList, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-table': {
            template: `
              <div class="el-table" :loading="loading">
                <div v-for="item in data" :key="item.id" class="el-table__row" data-test="data-row">
                  <slot :row="item"></slot>
                </div>
              </div>
            `,
            props: ['data', 'loading']
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot :row="$parent.row"></slot></div>',
            props: ['prop', 'label']
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot/></button>'
          },
          'el-input': {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-pagination': {
            template: '<div class="el-pagination"><slot/></div>',
            props: ['total', 'currentPage', 'pageSize'],
            emits: ['update:currentPage', 'update:pageSize']
          },
          'el-dialog': {
            template: '<div v-if="modelValue" class="el-dialog" data-test="detail-dialog"><slot/></div>',
            props: ['modelValue', 'title'],
            emits: ['update:modelValue']
          }
        },
        mocks: {
          ElMessageBox
        }
      }
    })

    await nextTick()
  })

  afterEach(() => {
    wrapper.unmount()
    vi.clearAllMocks()
  })

  it('应该正确渲染数据列表', () => {
    const rows = wrapper.findAll('[data-test="data-row"]')
    expect(rows).toHaveLength(2)
  })

  it('应该能预览数据内容', async () => {
    const viewButton = wrapper.find('[data-test="view-button"]')
    await viewButton.trigger('click')
    
    const dialog = wrapper.find('[data-test="detail-dialog"]')
    expect(dialog.exists()).toBe(true)
  })

  it('应该能删除数据', async () => {
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    await deleteButton.trigger('click')
    
    expect(store.deleteData).toHaveBeenCalledWith('1')
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })

  it('应该能导出数据', async () => {
    const exportButton = wrapper.find('[data-test="export-button"]')
    await exportButton.trigger('click')
    
    expect(store.exportData).toHaveBeenCalledWith({
      taskId: '1'
    })
    expect(ElMessage.success).toHaveBeenCalledWith('导出成功')
  })

  it('应该支持数据搜索', async () => {
    const searchInput = wrapper.find('[data-test="search-input"]')
    await searchInput.setValue('example')
    await nextTick()
    
    expect(store.fetchData).toHaveBeenCalledWith({
      taskId: '1',
      page: 1,
      pageSize: 10
    })
  })

  it('应该显示加载状态', async () => {
    await store.$patch({ loading: true })
    await nextTick()
    
    const table = wrapper.find('.el-table')
    expect(table.attributes('loading')).toBe('true')
  })

  it('应该显示错误信息', async () => {
    await store.$patch({ error: '获取数据失败' })
    await nextTick()
    
    const error = wrapper.find('[data-test="error-message"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toBe('获取数据失败')
  })
}) 