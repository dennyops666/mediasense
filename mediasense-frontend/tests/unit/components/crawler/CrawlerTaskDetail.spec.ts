import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import CrawlerTaskDetail from '@/components/crawler/CrawlerTaskDetail.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage } from 'element-plus'
import type { CrawlerTask } from '@/types/crawler'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('CrawlerTaskDetail.vue', () => {
  const mockTask: CrawlerTask = {
    id: '1',
    name: '测试任务',
    type: 'news',
    schedule: '0 0 * * *',
    config: {},
    status: 'running',
    lastRunTime: '2024-03-20T10:00:00Z',
    count: 100,
    configId: '1',
    startTime: '2024-03-20T10:00:00Z',
    totalItems: 100,
    successItems: 80,
    failedItems: 20,
    createdAt: '2024-03-20T10:00:00Z',
    updatedAt: '2024-03-20T10:00:00Z'
  }

  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          currentTask: mockTask,
          loading: false
        }
      }
    })

    wrapper = mount(CrawlerTaskDetail, {
      props: {
        taskId: '1'
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-descriptions': true,
          'el-descriptions-item': true,
          'el-tag': true,
          'el-button': true,
          'el-progress': true
        }
      }
    })

    store = useCrawlerStore()
  })

  describe('任务详情渲染', () => {
    it('应该正确渲染任务基本信息', () => {
      const name = wrapper.find('[data-test="task-name"]')
      const type = wrapper.find('[data-test="task-type"]')
      const status = wrapper.find('[data-test="task-status"]')
      
      expect(name.text()).toBe('测试任务')
      expect(type.text()).toBe('新闻')
      expect(status.exists()).toBe(true)
    })

    it('应该显示任务进度', () => {
      const progress = wrapper.find('[data-test="task-progress"]')
      expect(progress.exists()).toBe(true)
      expect(progress.attributes('percentage')).toBe('80')
    })

    it('应该显示任务统计信息', () => {
      const total = wrapper.find('[data-test="total-items"]')
      const success = wrapper.find('[data-test="success-items"]')
      const failed = wrapper.find('[data-test="failed-items"]')
      
      expect(total.text()).toContain('100')
      expect(success.text()).toContain('80')
      expect(failed.text()).toContain('20')
    })

    it('应该显示任务时间信息', () => {
      const startTime = wrapper.find('[data-test="start-time"]')
      const lastRunTime = wrapper.find('[data-test="last-run-time"]')
      
      expect(startTime.text()).toContain('2024-03-20 10:00:00')
      expect(lastRunTime.text()).toContain('2024-03-20 10:00:00')
    })
  })

  describe('任务操作', () => {
    it('应该能启动任务', async () => {
      const startButton = wrapper.find('[data-test="start-task"]')
      await startButton.trigger('click')

      expect(store.startTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已启动')
    })

    it('应该能停止任务', async () => {
      const stopButton = wrapper.find('[data-test="stop-task"]')
      await stopButton.trigger('click')

      expect(store.stopTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已停止')
    })

    it('应该能删除任务', async () => {
      const deleteButton = wrapper.find('[data-test="delete-task"]')
      await deleteButton.trigger('click')

      expect(store.deleteTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已删除')
    })
  })

  describe('任务配置', () => {
    it('应该能查看任务配置', async () => {
      const configButton = wrapper.find('[data-test="view-config"]')
      await configButton.trigger('click')

      const configDialog = wrapper.find('[data-test="config-dialog"]')
      expect(configDialog.exists()).toBe(true)
      expect(configDialog.isVisible()).toBe(true)
    })

    it('应该能编辑任务配置', async () => {
      const editButton = wrapper.find('[data-test="edit-config"]')
      await editButton.trigger('click')

      expect(wrapper.emitted('edit-config')).toBeTruthy()
    })
  })

  describe('任务日志', () => {
    it('应该显示任务日志列表', () => {
      const logList = wrapper.find('[data-test="task-logs"]')
      expect(logList.exists()).toBe(true)
    })

    it('应该能刷新日志', async () => {
      const refreshButton = wrapper.find('[data-test="refresh-logs"]')
      await refreshButton.trigger('click')

      expect(store.fetchTaskLogs).toHaveBeenCalledWith('1')
    })

    it('应该能导出日志', async () => {
      const exportButton = wrapper.find('[data-test="export-logs"]')
      await exportButton.trigger('click')

      expect(store.exportTaskLogs).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('日志导出成功')
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该处理操作失败', async () => {
      store.startTask.mockRejectedValue(new Error('启动失败'))
      
      const startButton = wrapper.find('[data-test="start-task"]')
      await startButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('启动失败')
    })
  })

  describe('自动刷新', () => {
    it('应该定期刷新任务状态', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      
      vi.advanceTimersByTime(5000)
      expect(store.fetchTask).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })

    it('应该在组件卸载时停止刷新', () => {
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
      wrapper.unmount()
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })
}) 