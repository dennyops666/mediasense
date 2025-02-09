import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import Monitor from '@/views/monitor/Monitor.vue'
import { useMonitorStore } from '@/stores/monitor'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { nextTick } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

describe('Monitor.vue', () => {
  let wrapper: any
  let store: any

  const mockSystemMetrics = {
    cpu: {
      usage: 75,  // 修改为触发警告状态的值
      cores: 4,
      load: [1.5, 1.2, 1.0]
    },
    memory: {
      total: 1024 * 1024 * 1024 * 8,
      used: 1024 * 1024 * 1024 * 7.5, // 修改为触发危险状态的值
      usage: 95
    },
    disk: [{ mount: '/', total: 100, used: 45, usage: 45 }],
    network: {
      interfaces: [{
        name: 'eth0',
        upload: 1024,
        download: 2048,
        totalUpload: 10240,
        totalDownload: 20480
      }]
    }
  }

  const mockLogs = [
    { timestamp: '2024-01-01 12:00:00', level: 'info', message: '系统启动' },
    { timestamp: '2024-01-01 12:01:00', level: 'warning', message: '内存使用率超过70%' },
    { timestamp: '2024-01-01 12:02:00', level: 'error', message: '进程崩溃' }
  ]

  const mockProcesses = [
    { pid: 1, name: 'systemd', user: 'root', cpu: 0.1, memory: 1024 * 1024 * 10, status: 'running' },
    { pid: 100, name: 'nginx', user: 'www-data', cpu: 1.5, memory: 1024 * 1024 * 50, status: 'stopped' }
  ]

  beforeEach(() => {
    store = {
      fetchSystemMetrics: vi.fn().mockResolvedValue(mockSystemMetrics),
      fetchLogs: vi.fn().mockResolvedValue(mockLogs),
      fetchProcessList: vi.fn().mockResolvedValue(mockProcesses),
      killProcess: vi.fn().mockResolvedValue(true)
    }

    wrapper = mount(Monitor, {
      global: {
        plugins: [createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            monitor: {
              systemMetrics: mockSystemMetrics,
              logs: mockLogs,
              processList: mockProcesses
            }
          }
        })],
        components: ElementPlusIconsVue,
        stubs: {
          'el-loading': {
            template: '<div class="el-loading" v-if="$attrs.loading"><slot></slot></div>',
            props: ['loading']
          },
          'el-alert': {
            template: '<div class="el-alert" :title="title" :type="type" data-test="error-alert"><slot></slot></div>',
            props: ['title', 'type']
          },
          'el-card': {
            template: '<div><slot name="header"></slot><slot></slot></div>'
          },
          'el-table': {
            template: '<div class="el-table"><slot></slot></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot :row="row" v-for="row in $parent.$parent.data"></slot></div>',
            props: ['prop', 'label', 'width']
          },
          'el-button': {
            template: '<button :data-test="$attrs[\'data-test\']" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['loading', 'type', 'size', 'disabled']
          },
          'el-input': {
            template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" :data-test="$attrs[\'data-test\']" />',
            props: ['modelValue']
          },
          'el-row': {
            template: '<div><slot></slot></div>'
          },
          'el-col': {
            template: '<div><slot></slot></div>'
          }
        }
      }
    })

    // 初始化数据
    wrapper.vm.cpuUsage = mockSystemMetrics.cpu.usage
    wrapper.vm.cpuCores = mockSystemMetrics.cpu.cores
    wrapper.vm.memoryUsage = mockSystemMetrics.memory.usage
    wrapper.vm.totalMemory = mockSystemMetrics.memory.total
    wrapper.vm.logs = mockLogs
    wrapper.vm.processList = mockProcesses
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('应该正确渲染监控组件', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('[data-test="monitor-container"]').exists()).toBe(true)
    })

    it('应该显示系统指标卡片', () => {
      expect(wrapper.find('[data-test="cpu-card"]').exists()).toBe(true)
      expect(wrapper.find('[data-test="memory-card"]').exists()).toBe(true)
    })
  })

  describe('系统指标显示', () => {
    it('应该显示CPU使用率和状态', async () => {
      await wrapper.vm.refreshSystemMetrics()
      await nextTick()
      
      const cpuUsage = wrapper.find('[data-test="cpu-usage"]')
      const cpuHealth = wrapper.find('[data-test="cpu-health"]')
      expect(cpuUsage.exists()).toBe(true)
      expect(cpuHealth.exists()).toBe(true)
      expect(cpuUsage.text()).toBe('75%')
      expect(cpuHealth.attributes('type')).toBe('warning')
    })

    it('应该显示内存使用情况和状态', async () => {
      await wrapper.vm.refreshSystemMetrics()
      await nextTick()
      
      const memoryUsage = wrapper.find('[data-test="memory-usage"]')
      const memoryHealth = wrapper.find('[data-test="memory-health"]')
      expect(memoryUsage.exists()).toBe(true)
      expect(memoryHealth.exists()).toBe(true)
      expect(memoryUsage.text()).toBe('95%')
      expect(memoryHealth.attributes('type')).toBe('danger')
    })
  })

  describe('日志管理', () => {
    it('应该显示系统日志列表', async () => {
      await wrapper.vm.refreshLogs()
      await nextTick()
      
      const logsCard = wrapper.find('[data-test="logs-card"]')
      expect(logsCard.exists()).toBe(true)
      expect(store.fetchLogs).toHaveBeenCalled()
    })

    it('应该能刷新日志', async () => {
      const refreshButton = wrapper.find('[data-test="refresh-logs-button"]')
      expect(refreshButton.exists()).toBe(true)
      await refreshButton.trigger('click')
      expect(store.fetchLogs).toHaveBeenCalled()
    })

    it('应该正确显示日志级别标签', async () => {
      await wrapper.vm.refreshLogs()
      await nextTick()
      
      const logLevelTag = wrapper.find('[data-test="log-level-INFO"]')
      expect(logLevelTag.exists()).toBe(true)
      expect(logLevelTag.attributes('type')).toBe('info')
    })
  })

  describe('进程管理', () => {
    it('应该显示进程列表', async () => {
      await wrapper.vm.refreshProcessList()
      await nextTick()
      
      const processCard = wrapper.find('[data-test="process-card"]')
      expect(processCard.exists()).toBe(true)
      expect(store.fetchProcessList).toHaveBeenCalled()
      expect(wrapper.vm.processList).toEqual(mockProcesses)
    })

    it('应该能搜索进程', async () => {
      await wrapper.vm.refreshProcessList()
      await nextTick()

      const searchInput = wrapper.find('[data-test="process-search"]')
      expect(searchInput.exists()).toBe(true)
      await searchInput.setValue('nginx')
      await nextTick()
      
      expect(wrapper.vm.processSearch).toBe('nginx')
      expect(wrapper.vm.filteredProcessList.length).toBe(1)
      expect(wrapper.vm.filteredProcessList[0].name).toBe('nginx')
    })

    it('应该能终止进程', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm')
      await wrapper.vm.refreshProcessList()
      await nextTick()
      
      const killButton = wrapper.find('[data-test="kill-process-100"]')
      expect(killButton.exists()).toBe(true)
      
      await killButton.trigger('click')
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(store.killProcess).toHaveBeenCalledWith(100)
      expect(ElMessage.success).toHaveBeenCalledWith('进程已终止')
    })

    it('应该正确处理进程终止取消', async () => {
      vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce('cancel')
      await wrapper.vm.refreshProcessList()
      await nextTick()
      
      const killButton = wrapper.find('[data-test="kill-process-100"]')
      expect(killButton.exists()).toBe(true)
      await killButton.trigger('click')
      
      expect(store.killProcess).not.toHaveBeenCalled()
    })

    it('应该正确处理进程终止失败', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm')
      store.killProcess.mockRejectedValueOnce(new Error('终止失败'))
      await wrapper.vm.refreshProcessList()
      await nextTick()
      
      const killButton = wrapper.find('[data-test="kill-process-100"]')
      expect(killButton.exists()).toBe(true)
      await killButton.trigger('click')
      
      expect(ElMessage.error).toHaveBeenCalledWith('终止进程失败')
    })
  })

  describe('状态处理', () => {
    it('应该显示加载状态', async () => {
      await wrapper.vm.$nextTick()
      wrapper.vm.loading = true
      await nextTick()
      
      const loadingIndicator = wrapper.find('.el-loading')
      expect(loadingIndicator.exists()).toBe(true)
    })

    it('应该显示错误信息', async () => {
      const errorMessage = '获取系统指标失败'
      wrapper.vm.error = errorMessage
      await nextTick()
      
      const errorAlert = wrapper.find('.el-alert')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.attributes('title')).toBe(errorMessage)
    })
  })

  describe('健康状态', () => {
    it('应该正确计算CPU健康状态', async () => {
      await store.$patch({ 
        systemMetrics: { 
          ...mockSystemMetrics,
          cpu: { ...mockSystemMetrics.cpu, usage: 85 }
        }
      })
      await nextTick()
      const cpuHealth = wrapper.find('[data-test="cpu-health"]')
      expect(cpuHealth.exists()).toBe(true)
      expect(cpuHealth.attributes('type')).toBe('warning')
    })

    it('应该正确计算内存健康状态', async () => {
      await store.$patch({ 
        systemMetrics: { 
          ...mockSystemMetrics,
          memory: { ...mockSystemMetrics.memory, usage: 95 }
        }
      })
      await nextTick()
      const memoryHealth = wrapper.find('[data-test="memory-health"]')
      expect(memoryHealth.exists()).toBe(true)
      expect(memoryHealth.attributes('type')).toBe('danger')
    })
  })

  describe('自动刷新', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('应该定期刷新系统指标', async () => {
      wrapper.vm.startAutoRefresh()
      
      await vi.advanceTimersByTime(5000)
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
    })

    it('应该在组件卸载时停止刷新', () => {
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
      wrapper.unmount()
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该处理获取系统指标失败', async () => {
      store.fetchSystemMetrics.mockRejectedValueOnce(new Error('获取失败'))
      await wrapper.vm.refreshSystemMetrics()
      await nextTick()
      
      expect(wrapper.vm.error).toBe('获取系统指标失败')
      expect(wrapper.vm.loading).toBe(false)
    })

    it('应该处理获取日志失败', async () => {
      store.fetchLogs.mockRejectedValueOnce(new Error('获取失败'))
      await wrapper.vm.refreshLogs()
      await nextTick()
      
      expect(wrapper.vm.error).toBe('获取日志失败')
      expect(wrapper.vm.loading).toBe(false)
    })

    it('应该处理获取进程列表失败', async () => {
      store.fetchProcessList.mockRejectedValueOnce(new Error('获取失败'))
      await wrapper.vm.refreshProcessList()
      await nextTick()
      
      expect(wrapper.vm.error).toBe('获取进程列表失败')
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('数据刷新', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('应该在挂载时获取所有数据', async () => {
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
      expect(store.fetchLogs).toHaveBeenCalled()
      expect(store.fetchProcessList).toHaveBeenCalled()
    })

    it('应该定期刷新系统指标', async () => {
      wrapper.vm.startAutoRefresh()
      await vi.advanceTimersByTime(5000)
      
      expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(2)
    })

    it('应该在组件卸载时停止刷新', () => {
      wrapper.vm.startAutoRefresh()
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval')
      
      wrapper.unmount()
      
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })
})