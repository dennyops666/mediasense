import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Monitor from '@/views/monitor/Monitor.vue'
import { useMonitorStore } from '@/stores/monitor'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'

// Mock ECharts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'v-chart',
    template: '<div class="echarts-mock"></div>'
  }
}))

describe('Monitor.vue', () => {
  let wrapper
  let store

  beforeEach(() => {
    wrapper = mount(Monitor, {
      global: {
        plugins: [createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            monitor: {
              metrics: {
                cpu: { usage: 45.5, cores: 4, temperature: 70 },
                memory: { total: 16384, used: 8192, free: 8192 },
                disk: { total: 512000, used: 256000, free: 256000 },
                network: { rx_bytes: 1024, tx_bytes: 2048, connections: 100 }
              },
              logs: [],
              loading: false,
              error: null
            }
          }
        })]
      },
      stubs: {
        'el-card': true,
        'el-row': true,
        'el-col': true,
        'el-button': true,
        'el-button-group': true,
        'el-icon': true
      }
    })
    store = useMonitorStore()
  })

  // 基础渲染测试
  describe('基础渲染', () => {
    it('渲染所有监控卡片', () => {
      expect(wrapper.find('.overview-card').exists()).toBe(true)
      expect(wrapper.findAll('.stat-card')).toHaveLength(4)
    })

    it('显示正确的系统指标', () => {
      expect(wrapper.find('[data-test="cpu-usage"]').text()).toContain('45.5%')
      expect(wrapper.find('[data-test="memory-usage"]').text()).toContain('50%')
      expect(wrapper.find('[data-test="disk-usage"]').text()).toContain('50%')
      expect(wrapper.find('[data-test="process-count"]').text()).toBe('100')
    })
  })

  // 数据加载测试
  describe('数据加载', () => {
    it('初始化时加载数据', () => {
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
      expect(store.fetchSystemLogs).toHaveBeenCalled()
    })

    it('定期更新数据', async () => {
      vi.useFakeTimers()
      const fetchMetrics = vi.spyOn(store, 'fetchSystemMetrics')
      
      await vi.advanceTimersByTime(2000)
      expect(fetchMetrics).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })
  })

  // 图表测试
  describe('图表显示', () => {
    it('渲染CPU和内存使用率图表', () => {
      const charts = wrapper.findAll('.chart')
      expect(charts).toHaveLength(2)
    })

    it('更新图表数据', async () => {
      const newMetrics = {
        cpu: { usage: 60 },
        memory: { used: 12288, total: 16384 }
      }
      
      await store.$patch({
        metrics: newMetrics
      })
      await nextTick()
      
      const cpuChart = wrapper.find('[data-test="cpu-chart"]')
      const memoryChart = wrapper.find('[data-test="memory-chart"]')
      
      expect(cpuChart.exists()).toBe(true)
      expect(memoryChart.exists()).toBe(true)
    })
  })

  // 日志过滤测试
  describe('日志过滤', () => {
    it('根据日志级别过滤', async () => {
      const logFilter = wrapper.find('[data-test="log-level-filter"]')
      await logFilter.trigger('click')
      
      expect(store.fetchSystemLogs).toHaveBeenCalledWith(
        expect.objectContaining({ level: 'error' })
      )
    })

    it('分页加载日志', async () => {
      const pagination = wrapper.find('[data-test="log-pagination"]')
      await pagination.trigger('current-change', 2)
      
      expect(store.fetchSystemLogs).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      )
    })
  })

  // 时间周期选择测试
  describe('时间周期选择', () => {
    it('切换时间周期', async () => {
      const periodButton = wrapper.find('[data-test="period-1h"]')
      await periodButton.trigger('click')
      
      expect(wrapper.vm.currentPeriod).toBe('1h')
      expect(store.fetchSystemMetrics).toHaveBeenCalledWith(
        expect.objectContaining({ period: '1h' })
      )
    })
  })

  // 错误处理测试
  describe('错误处理', () => {
    it('显示加载错误信息', async () => {
      await store.$patch({
        error: '获取系统指标失败'
      })
      
      expect(wrapper.find('[data-test="error-message"]').exists()).toBe(true)
      expect(wrapper.find('[data-test="error-message"]').text()).toContain('获取系统指标失败')
    })

    it('提供重试选项', async () => {
      await store.$patch({
        error: '获取系统指标失败'
      })
      
      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')
      
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
    })
  })

  // 清理测试
  describe('组件清理', () => {
    it('卸载时清理定时器', () => {
      const clearInterval = vi.spyOn(window, 'clearInterval')
      wrapper.unmount()
      expect(clearInterval).toHaveBeenCalled()
    })
  })
}) 