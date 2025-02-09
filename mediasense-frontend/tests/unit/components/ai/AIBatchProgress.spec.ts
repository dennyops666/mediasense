import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import AIBatchProgress from '@/components/ai/AIBatchProgress.vue'
import { useAIStore } from '@/stores/ai'
import { ElMessage } from 'element-plus'
import { nextTick } from 'vue'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('AIBatchProgress.vue', () => {
  const mockBatchTasks = [
    {
      id: '1',
      name: '批量分析任务1',
      status: 'running',
      progress: 60,
      total: 100,
      completed: 60,
      failed: 5,
      startTime: '2024-03-20T10:00:00Z',
      endTime: null
    },
    {
      id: '2',
      name: '批量分析任务2',
      status: 'completed',
      progress: 100,
      total: 50,
      completed: 48,
      failed: 2,
      startTime: '2024-03-20T09:00:00Z',
      endTime: '2024-03-20T09:30:00Z'
    }
  ]

  let wrapper: any
  let store: any

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        ai: {
          batchTasks: mockBatchTasks,
          loading: false,
          error: null
        }
      }
    })

    store = useAIStore(pinia)

    // 模拟 store 方法
    store.pauseBatchTask.mockResolvedValue(undefined)
    store.resumeBatchTask.mockResolvedValue(undefined)
    store.cancelBatchTask.mockResolvedValue(undefined)
    store.retryBatchTask.mockResolvedValue(undefined)
    store.fetchBatchTasks.mockResolvedValue(mockBatchTasks)

    wrapper = mount(AIBatchProgress, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-progress': {
            template: '<div class="el-progress" :data-percentage="percentage"><slot></slot></div>',
            props: ['percentage']
          },
          'el-tag': {
            template: '<span class="el-tag"><slot></slot></span>'
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot></slot></button>'
          },
          'el-dialog': {
            template: '<div v-if="modelValue" class="el-dialog"><slot></slot></div>',
            props: ['modelValue']
          },
          'el-select': {
            template: '<select v-model="value" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', value)
                }
              }
            }
          },
          'el-option': {
            template: '<option :value="value"><slot></slot></option>',
            props: ['value']
          },
          'el-input': {
            template: '<input v-model="value" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', value)
                }
              }
            }
          }
        }
      }
    })

    await nextTick()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('任务列表渲染', () => {
    it('应该正确渲染批量任务列表', () => {
      const tasks = wrapper.findAll('[data-test="batch-task"]')
      expect(tasks).toHaveLength(2)
    })

    it('应该显示任务进度', () => {
      const progress = wrapper.findAll('.el-progress')
      expect(progress[0].attributes('data-percentage')).toBe('60')
      expect(progress[1].attributes('data-percentage')).toBe('100')
    })

    it('应该显示任务状态标签', () => {
      const status = wrapper.findAll('.el-tag')
      expect(status[0].text()).toContain('进行中')
      expect(status[1].text()).toContain('已完成')
    })

    it('应该显示任务统计信息', () => {
      const stats = wrapper.find('[data-test="task-stats"]')
      expect(stats.text()).toContain('总任务数: 150')
      expect(stats.text()).toContain('已完成: 108')
      expect(stats.text()).toContain('失败: 7')
    })
  })

  describe('任务操作', () => {
    it('应该能暂停任务', async () => {
      const pauseButton = wrapper.find('[data-test="pause-task-1"]')
      await pauseButton.trigger('click')
      await nextTick()

      expect(store.pauseBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已暂停')
    })

    it('应该能恢复任务', async () => {
      store.$patch({
        batchTasks: [{
          ...mockBatchTasks[0],
          status: 'paused'
        }]
      })
      await nextTick()

      const resumeButton = wrapper.find('[data-test="resume-task-1"]')
      await resumeButton.trigger('click')
      await nextTick()

      expect(store.resumeBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已恢复')
    })

    it('应该能取消任务', async () => {
      const cancelButton = wrapper.find('[data-test="cancel-task-1"]')
      await cancelButton.trigger('click')
      await nextTick()

      expect(store.cancelBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已取消')
    })

    it('应该能重试失败的任务', async () => {
      store.$patch({
        batchTasks: [{
          ...mockBatchTasks[0],
          status: 'failed'
        }]
      })
      await nextTick()

      const retryButton = wrapper.find('[data-test="retry-task-1"]')
      await retryButton.trigger('click')
      await nextTick()

      expect(store.retryBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已重试')
    })
  })

  describe('任务详情', () => {
    it('应该显示任务详细信息', async () => {
      const detailButton = wrapper.find('[data-test="view-detail-1"]')
      await detailButton.trigger('click')
      await nextTick()

      const dialog = wrapper.find('.el-dialog')
      expect(dialog.exists()).toBe(true)
      expect(dialog.text()).toContain('批量分析任务1')
    })

    it('应该显示任务执行时间', () => {
      const times = wrapper.findAll('[data-test="task-time"]')
      expect(times[0].text()).toContain('2024-03-20 10:00:00')
      expect(times[1].text()).toContain('2024-03-20 09:30:00')
    })
  })

  describe('自动刷新', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('应该定期刷新任务状态', async () => {
      wrapper.vm.startAutoRefresh()
      
      await vi.advanceTimersByTime(5000)
      expect(store.fetchBatchTasks).toHaveBeenCalledTimes(2)
    })

    it('应该在组件卸载时停止刷新', () => {
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
      wrapper.unmount()
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      store.$patch({ error: '加载失败' })
      await nextTick()
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该处理操作失败', async () => {
      store.pauseBatchTask.mockRejectedValueOnce(new Error('暂停失败'))
      
      const pauseButton = wrapper.find('[data-test="pause-task-1"]')
      await pauseButton.trigger('click')
      await nextTick()

      expect(ElMessage.error).toHaveBeenCalledWith('暂停失败')
    })
  })

  describe('任务过滤', () => {
    it('应该能按状态过滤任务', async () => {
      const statusFilter = wrapper.find('[data-test="status-filter"]')
      await statusFilter.setValue('running')
      await statusFilter.trigger('change')
      await nextTick()

      const tasks = wrapper.findAll('[data-test="batch-task"]')
      expect(tasks).toHaveLength(1)
      expect(tasks[0].text()).toContain('批量分析任务1')
    })

    it('应该能按名称搜索任务', async () => {
      const searchInput = wrapper.find('[data-test="task-search"]')
      await searchInput.setValue('任务1')
      await searchInput.trigger('input')
      await nextTick()

      const tasks = wrapper.findAll('[data-test="batch-task"]')
      expect(tasks).toHaveLength(1)
      expect(tasks[0].text()).toContain('批量分析任务1')
    })
  })
})
