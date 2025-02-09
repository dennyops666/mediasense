import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import CrawlerTaskList from '@/components/crawler/CrawlerTaskList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

describe('CrawlerTaskList.vue', () => {
  let wrapper
  let store

  const mockTasks = [
    {
      id: '1',
      configId: '1',
      status: 'running',
      progress: 50,
      createdAt: '2024-03-20 10:00:00',
      updatedAt: '2024-03-20 10:30:00'
    },
    {
      id: '2',
      configId: '1',
      status: 'stopped',
      progress: 100,
      createdAt: '2024-03-20 11:00:00',
      updatedAt: '2024-03-20 11:30:00'
    }
  ]

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          tasks: mockTasks,
          loading: false,
          error: null
        }
      }
    })

    store = useCrawlerStore(pinia)
    store.fetchTasks = vi.fn().mockResolvedValue(mockTasks)
    store.startTask = vi.fn().mockResolvedValue()
    store.stopTask = vi.fn().mockResolvedValue()
    store.deleteTask = vi.fn().mockResolvedValue()

    wrapper = mount(CrawlerTaskList, {
      props: {
        configId: '1'
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-table': {
            template: `
              <div class="el-table" :loading="loading">
                <div v-for="item in data" :key="item.id" class="el-table__row" data-test="task-row">
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
            template: '<button @click="$emit(\'click\')"><slot/></button>',
            props: ['type', 'link']
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type"><slot/></span>',
            props: ['type']
          },
          'el-progress': {
            template: '<div class="el-progress" :percentage="percentage"><slot/></div>',
            props: ['percentage']
          }
        }
      }
    })

    await nextTick()
  })

  afterEach(() => {
    wrapper.unmount()
    vi.clearAllMocks()
  })

  it('应该正确渲染任务列表', () => {
    const rows = wrapper.findAll('[data-test="task-row"]')
    expect(rows).toHaveLength(2)
  })

  it('应该正确显示任务状态', () => {
    const tags = wrapper.findAll('.el-tag')
    expect(tags[0].text()).toBe('running')
    expect(tags[1].text()).toBe('stopped')
  })

  it('应该能启动任务', async () => {
    const startButton = wrapper.find('[data-test="start-button"]')
    await startButton.trigger('click')
    
    expect(store.startTask).toHaveBeenCalledWith('1')
  })

  it('应该能停止任务', async () => {
    const stopButton = wrapper.find('[data-test="stop-button"]')
    await stopButton.trigger('click')
    
    expect(store.stopTask).toHaveBeenCalledWith('1')
  })

  it('应该能删除任务', async () => {
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    await deleteButton.trigger('click')
    
    expect(store.deleteTask).toHaveBeenCalledWith('1')
  })

  it('应该显示加载状态', async () => {
    await store.$patch({ loading: true })
    await nextTick()
    
    const table = wrapper.find('.el-table')
    expect(table.attributes('loading')).toBe('true')
  })

  it('应该显示错误信息', async () => {
    await store.$patch({ error: '获取任务失败' })
    await nextTick()
    
    const error = wrapper.find('[data-test="error-message"]')
    expect(error.exists()).toBe(true)
    expect(error.text()).toBe('获取任务失败')
  })
}) 