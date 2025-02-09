import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/dashboard/Dashboard.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useMonitorStore } from '@/stores/monitor'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('仪表盘集成测试', () => {
  let router: any
  let dashboardStore: any
  let monitorStore: any
  let crawlerStore: any
  let wrapper: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/dashboard',
          component: Dashboard
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        dashboard: {
          statistics: {
            totalTasks: 100,
            runningTasks: 10,
            totalData: 5000,
            todayData: 200
          },
          recentAlerts: [
            { id: 1, message: '系统负载过高', level: 'warning', time: '2024-03-20T10:00:00Z' },
            { id: 2, message: '新任务创建', level: 'info', time: '2024-03-20T09:00:00Z' }
          ],
          loading: false
        },
        monitor: {
          systemStatus: {
            cpu: 60,
            memory: 70,
            disk: 50
          }
        },
        crawler: {
          activeTasks: [
            { id: 1, name: '任务1', status: 'running', progress: 60 },
            { id: 2, name: '任务2', status: 'paused', progress: 30 }
          ]
        }
      }
    })

    wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'el-card': true,
          'el-table': true,
          'el-progress': true,
          'echarts': true
        }
      }
    })

    dashboardStore = useDashboardStore()
    monitorStore = useMonitorStore()
    crawlerStore = useCrawlerStore()
  })

  describe('数据概览展示', () => {
    it('应该显示关键统计数据', () => {
      const stats = wrapper.find('[data-test="statistics"]')
      expect(stats.text()).toContain('100')
      expect(stats.text()).toContain('10')
      expect(stats.text()).toContain('5000')
      expect(stats.text()).toContain('200')
    })

    it('应该显示系统状态', () => {
      const status = wrapper.find('[data-test="system-status"]')
      expect(status.text()).toContain('60%')
      expect(status.text()).toContain('70%')
      expect(status.text()).toContain('50%')
    })

    it('应该显示最近告警', () => {
      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(2)
      expect(alerts[0].text()).toContain('系统负载过高')
    })

    it('应该显示活跃任务', () => {
      const tasks = wrapper.findAll('[data-test="task-item"]')
      expect(tasks).toHaveLength(2)
      expect(tasks[0].text()).toContain('任务1')
    })
  })

  describe('快捷操作功能', () => {
    it('应该能快速创建任务', async () => {
      const createButton = wrapper.find('[data-test="quick-create"]')
      await createButton.trigger('click')

      const form = wrapper.find('[data-test="quick-form"]')
      await form.setValue({
        name: '新任务',
        type: 'news'
      })
      await form.trigger('submit')

      expect(crawlerStore.createTask).toHaveBeenCalledWith({
        name: '新任务',
        type: 'news'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('任务已创建')
    })

    it('应该能快速查看报告', async () => {
      const reportButton = wrapper.find('[data-test="view-report"]')
      await reportButton.trigger('click')

      const report = wrapper.find('[data-test="report-dialog"]')
      expect(report.exists()).toBe(true)
      expect(report.isVisible()).toBe(true)
    })

    it('应该能快速处理告警', async () => {
      const alertAction = wrapper.find('[data-test="handle-alert-1"]')
      await alertAction.trigger('click')

      expect(monitorStore.acknowledgeAlert).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('告警已处理')
    })
  })

  describe('组件联动', () => {
    it('应该在创建任务后更新统计数据', async () => {
      const createButton = wrapper.find('[data-test="quick-create"]')
      await createButton.trigger('click')

      const form = wrapper.find('[data-test="quick-form"]')
      await form.setValue({
        name: '新任务',
        type: 'news'
      })
      await form.trigger('submit')

      expect(dashboardStore.fetchStatistics).toHaveBeenCalled()
    })

    it('应该在处理告警后更新告警列表', async () => {
      const alertAction = wrapper.find('[data-test="handle-alert-1"]')
      await alertAction.trigger('click')

      expect(dashboardStore.fetchRecentAlerts).toHaveBeenCalled()
    })

    it('应该在任务状态变化时更新活跃任务', async () => {
      const taskAction = wrapper.find('[data-test="pause-task-1"]')
      await taskAction.trigger('click')

      expect(dashboardStore.fetchActiveTasks).toHaveBeenCalled()
    })
  })

  describe('数据实时更新', () => {
    it('应该定期刷新系统状态', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      
      vi.advanceTimersByTime(30000)
      expect(monitorStore.fetchSystemStatus).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })

    it('应该定期刷新活跃任务状态', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      
      vi.advanceTimersByTime(30000)
      expect(crawlerStore.fetchActiveTasks).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })

    it('应该在组件卸载时停止刷新', () => {
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
      wrapper.unmount()
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该在加载失败时显示重试按钮', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')

      expect(dashboardStore.fetchStatistics).toHaveBeenCalled()
      expect(monitorStore.fetchSystemStatus).toHaveBeenCalled()
      expect(crawlerStore.fetchActiveTasks).toHaveBeenCalled()
    })

    it('应该处理部分数据加载失败', async () => {
      dashboardStore.fetchStatistics.mockRejectedValue(new Error('统计数据加载失败'))
      
      await wrapper.vm.loadData()
      
      const partialError = wrapper.find('[data-test="partial-error"]')
      expect(partialError.exists()).toBe(true)
      expect(partialError.text()).toContain('部分数据加载失败')
    })
  })
}) 