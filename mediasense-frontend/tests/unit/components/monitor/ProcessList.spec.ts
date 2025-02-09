import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import ProcessList from '@/components/monitor/ProcessList.vue'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'
import type { Process } from '@/types/monitor'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('ProcessList.vue', () => {
  const mockProcesses: Process[] = [
    {
      pid: 1234,
      name: 'node',
      cpu: 2.5,
      memory: 150.5,
      status: 'running',
      startTime: '2024-03-20T10:00:00Z'
    },
    {
      pid: 5678,
      name: 'python',
      cpu: 1.8,
      memory: 200.3,
      status: 'sleeping',
      startTime: '2024-03-20T09:00:00Z'
    }
  ]

  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          processes: mockProcesses,
          loading: false
        }
      }
    })

    wrapper = mount(ProcessList, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-button': true,
          'el-pagination': true
        }
      }
    })

    store = useMonitorStore()
  })

  describe('进程列表渲染', () => {
    it('应该正确渲染进程列表', () => {
      const processes = wrapper.findAll('[data-test="process-item"]')
      expect(processes).toHaveLength(mockProcesses.length)
    })

    it('应该显示进程状态标签', () => {
      const statusTags = wrapper.findAll('[data-test="process-status"]')
      expect(statusTags[0].text()).toBe('运行中')
      expect(statusTags[1].text()).toBe('休眠')
    })

    it('应该显示进程资源使用情况', () => {
      const cpuUsage = wrapper.findAll('[data-test="process-cpu"]')
      const memoryUsage = wrapper.findAll('[data-test="process-memory"]')
      
      expect(cpuUsage[0].text()).toContain('2.5%')
      expect(memoryUsage[0].text()).toContain('150.5 MB')
    })

    it('应该显示进程启动时间', () => {
      const startTimes = wrapper.findAll('[data-test="process-start-time"]')
      expect(startTimes[0].text()).toContain('2024-03-20 10:00:00')
    })
  })

  describe('进程操作', () => {
    it('应该能终止进程', async () => {
      const killButton = wrapper.find('[data-test="kill-process-1234"]')
      await killButton.trigger('click')

      expect(store.killProcess).toHaveBeenCalledWith(1234)
      expect(ElMessage.success).toHaveBeenCalledWith('已终止进程')
    })

    it('应该能重启进程', async () => {
      const restartButton = wrapper.find('[data-test="restart-process-1234"]')
      await restartButton.trigger('click')

      expect(store.restartProcess).toHaveBeenCalledWith(1234)
      expect(ElMessage.success).toHaveBeenCalledWith('已重启进程')
    })
  })

  describe('进程过滤', () => {
    it('应该能按名称搜索进程', async () => {
      const searchInput = wrapper.find('[data-test="process-search"]')
      await searchInput.setValue('node')
      await searchInput.trigger('input')

      const processes = wrapper.findAll('[data-test="process-item"]')
      expect(processes).toHaveLength(1)
    })

    it('应该能按状态过滤进程', async () => {
      const statusFilter = wrapper.find('[data-test="status-filter"]')
      await statusFilter.setValue('running')
      await statusFilter.trigger('change')

      const processes = wrapper.findAll('[data-test="process-item"]')
      expect(processes).toHaveLength(1)
    })

    it('应该能按资源使用率排序', async () => {
      const cpuSort = wrapper.find('[data-test="cpu-sort"]')
      await cpuSort.trigger('click')

      expect(wrapper.vm.sortBy).toBe('cpu')
      expect(wrapper.vm.sortOrder).toBe('descending')
    })
  })

  describe('自动刷新', () => {
    it('应该定期刷新进程列表', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      
      vi.advanceTimersByTime(30000)
      expect(store.fetchProcesses).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })

    it('应该能停止自动刷新', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      wrapper.vm.stopAutoRefresh()
      
      vi.advanceTimersByTime(30000)
      expect(store.fetchProcesses).toHaveBeenCalledTimes(1)
      
      vi.useRealTimers()
    })
  })

  describe('加载状态', () => {
    it('应该显示加载状态', async () => {
      await wrapper.setData({ loading: true })
      
      const loading = wrapper.find('[data-test="loading"]')
      expect(loading.exists()).toBe(true)
    })

    it('加载失败时应该显示错误信息', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })
  })
}) 