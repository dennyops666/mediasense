import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import MonitorDashboard from '@/views/monitor/MonitorDashboard.vue'
import { useMonitorStore } from '@/stores/monitor'
import { createTestingPinia } from '@pinia/testing'

describe('MonitorDashboard', () => {
  let wrapper
  let store

  beforeEach(() => {
    wrapper = mount(MonitorDashboard, {
      global: {
        plugins: [createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            monitor: {
              metrics: null,
              logs: [],
              processes: [],
              diskUsage: [],
              loading: false,
              error: null
            }
          }
        })]
      }
    })
    store = useMonitorStore()
  })

  it('renders dashboard components', () => {
    expect(wrapper.find('[data-test="system-resource-monitor"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="system-logs"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="process-list"]').exists()).toBe(true)
  })

  it('loads initial data on mount', () => {
    expect(store.fetchSystemMetrics).toHaveBeenCalled()
    expect(store.fetchSystemLogs).toHaveBeenCalled()
    expect(store.fetchProcessList).toHaveBeenCalled()
  })

  it('displays loading state', async () => {
    await store.$patch({ loading: true })
    expect(wrapper.find('[data-test="loading-indicator"]').exists()).toBe(true)
  })

  it('displays error message when loading fails', async () => {
    await store.$patch({ error: 'Failed to load dashboard data' })
    expect(wrapper.find('[data-test="error-message"]').exists()).toBe(true)
  })

  it('refreshes data when refresh button clicked', async () => {
    const refreshButton = wrapper.find('[data-test="refresh-button"]')
    await refreshButton.trigger('click')
    
    expect(store.fetchSystemMetrics).toHaveBeenCalled()
    expect(store.fetchSystemLogs).toHaveBeenCalled()
    expect(store.fetchProcessList).toHaveBeenCalled()
  })

  it('filters system logs', async () => {
    const logFilter = wrapper.find('[data-test="log-filter"]')
    await logFilter.setValue('error')
    
    expect(store.fetchSystemLogs).toHaveBeenCalledWith(
      expect.objectContaining({ filter: 'error' })
    )
  })

  it('sorts process list', async () => {
    const sortButton = wrapper.find('[data-test="sort-cpu-usage"]')
    await sortButton.trigger('click')
    
    expect(wrapper.vm.sortedProcesses[0].cpu).toBeGreaterThanOrEqual(
      wrapper.vm.sortedProcesses[1].cpu
    )
  })

  it('exports dashboard data', async () => {
    const exportButton = wrapper.find('[data-test="export-button"]')
    await exportButton.trigger('click')
    
    expect(store.exportMonitoringData).toHaveBeenCalled()
  })
})

