import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SystemResourceMonitor from '@/components/monitor/SystemResourceMonitor.vue'
import { useMonitorStore } from '@/stores/monitor'
import { createTestingPinia } from '@pinia/testing'

describe('SystemResourceMonitor', () => {
  let wrapper
  let store

  beforeEach(() => {
    wrapper = mount(SystemResourceMonitor, {
      global: {
        plugins: [createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            monitor: {
              resources: {
                cpu: {
                  usage: 45.5,
                  cores: 4,
                  temperature: 65
                },
                memory: {
                  total: 16384,
                  used: 8192,
                  free: 8192
                },
                disk: {
                  total: 512000,
                  used: 256000,
                  free: 256000
                },
                network: {
                  upload: 1024,
                  download: 2048,
                  latency: 50
                }
              },
              lastUpdate: new Date().toISOString()
            }
          }
        })]
      }
    })
    store = useMonitorStore()
  })

  // 基础渲染测试
  it('renders all resource sections', () => {
    expect(wrapper.find('[data-test="cpu-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="memory-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="disk-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="network-section"]').exists()).toBe(true)
  })

  // CPU监控测试
  describe('CPU Monitoring', () => {
    it('displays correct CPU usage', () => {
      const cpuUsage = wrapper.find('[data-test="cpu-usage"]')
      expect(cpuUsage.text()).toContain('45.5%')
    })

    it('shows warning when CPU usage is high', async () => {
      await store.$patch({
        resources: {
          cpu: { usage: 85.5 }
        }
      })
      expect(wrapper.find('[data-test="cpu-warning"]').exists()).toBe(true)
    })

    it('updates CPU temperature in real-time', async () => {
      await store.$patch({
        resources: {
          cpu: { temperature: 75 }
        }
      })
      expect(wrapper.find('[data-test="cpu-temperature"]').text()).toContain('75°C')
    })
  })

  // 内存监控测试
  describe('Memory Monitoring', () => {
    it('displays correct memory usage percentage', () => {
      const memoryUsage = wrapper.find('[data-test="memory-usage"]')
      expect(memoryUsage.text()).toContain('50%') // 8192/16384 * 100
    })

    it('formats memory values properly', () => {
      const memoryTotal = wrapper.find('[data-test="memory-total"]')
      expect(memoryTotal.text()).toContain('16 GB')
    })

    it('shows alert when memory is nearly full', async () => {
      await store.$patch({
        resources: {
          memory: {
            total: 16384,
            used: 15000
          }
        }
      })
      expect(wrapper.find('[data-test="memory-alert"]').exists()).toBe(true)
    })
  })

  // 磁盘监控测试
  describe('Disk Monitoring', () => {
    it('displays correct disk usage', () => {
      const diskUsage = wrapper.find('[data-test="disk-usage"]')
      expect(diskUsage.text()).toContain('50%') // 256000/512000 * 100
    })

    it('shows warning when disk space is low', async () => {
      await store.$patch({
        resources: {
          disk: {
            total: 512000,
            free: 25600 // 5% free
          }
        }
      })
      expect(wrapper.find('[data-test="disk-warning"]').exists()).toBe(true)
    })
  })

  // 网络监控测试
  describe('Network Monitoring', () => {
    it('displays current network speeds', () => {
      const upload = wrapper.find('[data-test="network-upload"]')
      const download = wrapper.find('[data-test="network-download"]')
      expect(upload.text()).toContain('1.0 KB/s')
      expect(download.text()).toContain('2.0 KB/s')
    })

    it('shows latency status', () => {
      const latency = wrapper.find('[data-test="network-latency"]')
      expect(latency.text()).toContain('50ms')
    })

    it('indicates poor network conditions', async () => {
      await store.$patch({
        resources: {
          network: {
            latency: 200
          }
        }
      })
      expect(wrapper.find('[data-test="network-poor-condition"]').exists()).toBe(true)
    })
  })

  // 实时更新测试
  describe('Real-time Updates', () => {
    it('updates metrics periodically', async () => {
      const updateMetrics = vi.spyOn(store, 'fetchResourceMetrics')
      await wrapper.vm.$nextTick()
      expect(updateMetrics).toHaveBeenCalled()
    })

    it('displays last update time', () => {
      const lastUpdate = wrapper.find('[data-test="last-update"]')
      expect(lastUpdate.exists()).toBe(true)
      expect(lastUpdate.text()).toContain(new Date(store.lastUpdate).toLocaleTimeString())
    })
  })

  // 图表测试
  describe('Charts', () => {
    it('renders CPU usage chart', () => {
      expect(wrapper.find('[data-test="cpu-chart"]').exists()).toBe(true)
    })

    it('updates chart data in real-time', async () => {
      const newData = {
        cpu: { usage: 60 },
        timestamp: new Date().toISOString()
      }
      await store.$patch({
        resources: newData
      })
      const chart = wrapper.find('[data-test="cpu-chart"]')
      expect(chart.props('data')).toContainEqual(expect.objectContaining(newData))
    })
  })

  // 告警测试
  describe('Alerts', () => {
    it('triggers alert when thresholds are exceeded', async () => {
      await store.$patch({
        resources: {
          cpu: { usage: 95 },
          memory: { used: 15500, total: 16384 }
        }
      })
      const alerts = wrapper.findAll('[data-test="resource-alert"]')
      expect(alerts.length).toBeGreaterThan(0)
    })

    it('shows alert history', async () => {
      const showHistory = wrapper.find('[data-test="show-alert-history"]')
      await showHistory.trigger('click')
      expect(wrapper.find('[data-test="alert-history-modal"]').exists()).toBe(true)
    })
  })

  // 导出功能测试
  describe('Export Functionality', () => {
    it('exports monitoring data', async () => {
      const exportData = vi.spyOn(store, 'exportMonitoringData')
      const exportButton = wrapper.find('[data-test="export-data"]')
      await exportButton.trigger('click')
      expect(exportData).toHaveBeenCalled()
    })
  })

  // 错误处理测试
  describe('Error Handling', () => {
    it('displays error message when metrics fetch fails', async () => {
      vi.spyOn(store, 'fetchResourceMetrics').mockRejectedValueOnce(new Error('Fetch failed'))
      await wrapper.vm.$nextTick()
      expect(wrapper.find('[data-test="error-message"]').exists()).toBe(true)
    })

    it('retries failed metrics fetch', async () => {
      const fetchMetrics = vi.spyOn(store, 'fetchResourceMetrics')
      const retryButton = wrapper.find('[data-test="retry-fetch"]')
      await retryButton.trigger('click')
      expect(fetchMetrics).toHaveBeenCalledTimes(1)
    })
  })
}) 