import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import CrawlerTaskList from '@/components/crawler/CrawlerTaskList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerTask } from '@/types/crawler'

const mockTasks: CrawlerTask[] = [
  {
    id: '1',
    name: '测试任务1',
    type: 'news',
    status: 'running',
    progress: 50,
    startTime: '2024-01-01 12:00:00',
    endTime: null,
    runtime: '1小时',
    statistics: {
      total: 100,
      success: 50,
      failed: 0
    }
  },
  {
    id: '2',
    name: '测试任务2',
    type: 'news',
    status: 'stopped',
    progress: 100,
    startTime: '2024-01-02 12:00:00',
    endTime: '2024-01-02 13:00:00',
    runtime: '1小时',
    statistics: {
      total: 100,
      success: 100,
      failed: 0
    }
  }
]

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue('confirm')
  }
}))

describe('CrawlerTaskList 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(CrawlerTaskList, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                tasks: mockTasks,
                total: mockTasks.length,
                loading: false,
                error: null
              }
            }
          })
        ]
      }
    })
  }

  it('应该正确显示任务列表', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    const taskRows = wrapper.findAll('.task-row')
    expect(taskRows).toHaveLength(2)
    expect(taskRows[0].text()).toContain('测试任务1')
    expect(taskRows[1].text()).toContain('测试任务2')
  })

  it('应该能搜索任务', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    
    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('测试任务1')
    await wrapper.vm.$nextTick()
    
    expect(store.fetchTasks).toHaveBeenCalledWith(expect.objectContaining({
      keyword: '测试任务1'
    }))
  })

  it('应该能筛选任务状态', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    
    const statusSelect = wrapper.find('.status-select')
    await statusSelect.setValue('running')
    await wrapper.vm.$nextTick()
    
    expect(store.fetchTasks).toHaveBeenCalledWith(expect.objectContaining({
      status: 'running'
    }))
  })

  it('应该能启动任务', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    store.startTask = vi.fn().mockResolvedValue(undefined)
    
    const startButton = wrapper.find('.start-button')
    await startButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(store.startTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('任务启动成功')
  })

  it('应该能停止任务', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    store.stopTask = vi.fn().mockResolvedValue(undefined)
    
    const stopButton = wrapper.find('.stop-button')
    await stopButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(store.stopTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('任务停止成功')
  })

  it('应该能删除任务', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    store.deleteTask = vi.fn().mockResolvedValue(undefined)
    ElMessageBox.confirm = vi.fn().mockResolvedValue('confirm')
    
    const deleteButton = wrapper.find('.delete-button')
    await deleteButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(store.deleteTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })

  it('应该能批量启动任务', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    store.batchStartTasks = vi.fn().mockResolvedValue(undefined)
    
    // 选择任务
    const checkboxes = wrapper.findAll('.task-checkbox')
    await checkboxes[0].setChecked()
    await checkboxes[1].setChecked()
    await wrapper.vm.$nextTick()
    
    const batchStartButton = wrapper.find('.batch-start-button')
    await batchStartButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(store.batchStartTasks).toHaveBeenCalledWith(['1', '2'])
    expect(ElMessage.success).toHaveBeenCalledWith('批量启动成功')
  })

  it('应该正确处理错误状态', async () => {
    const wrapper = createWrapper()
    const store = useCrawlerStore()
    store.$patch({ error: '获取任务列表失败' })
    await wrapper.vm.$nextTick()

    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('获取任务列表失败')
  })
}) 