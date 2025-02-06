import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMonitor } from '@/composables/useMonitor'
import { useMonitorStore } from '@/stores/monitor'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/monitor', () => ({
  useMonitorStore: vi.fn()
}))

describe('useMonitor', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializes with default values', () => {
    const mockStore = {
      metrics: null,
      logs: [],
      processes: [],
      loading: false,
      error: null,
      fetchSystemMetrics: vi.fn(),
      fetchSystemLogs: vi.fn(),
      fetchProcessList: vi.fn()
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { metrics, logs, processes, loading, error } = useMonitor()

    expect(metrics.value).toBeNull()
    expect(logs.value).toEqual([])
    expect(processes.value).toEqual([])
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('fetches initial data', async () => {
    const mockStore = {
      fetchSystemMetrics: vi.fn(),
      fetchSystemLogs: vi.fn(),
      fetchProcessList: vi.fn()
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { fetchInitialData } = useMonitor()
    await fetchInitialData()

    expect(mockStore.fetchSystemMetrics).toHaveBeenCalled()
    expect(mockStore.fetchSystemLogs).toHaveBeenCalled()
    expect(mockStore.fetchProcessList).toHaveBeenCalled()
  })

  it('refreshes data', async () => {
    const mockStore = {
      fetchSystemMetrics: vi.fn(),
      fetchSystemLogs: vi.fn(),
      fetchProcessList: vi.fn()
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { refreshData } = useMonitor()
    await refreshData()

    expect(mockStore.fetchSystemMetrics).toHaveBeenCalled()
    expect(mockStore.fetchSystemLogs).toHaveBeenCalled()
    expect(mockStore.fetchProcessList).toHaveBeenCalled()
  })

  it('starts and stops auto refresh', () => {
    vi.useFakeTimers()
    const mockStore = {
      fetchSystemMetrics: vi.fn(),
      fetchSystemLogs: vi.fn(),
      fetchProcessList: vi.fn()
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { startAutoRefresh, stopAutoRefresh } = useMonitor()
    
    startAutoRefresh()
    vi.advanceTimersByTime(60000)
    expect(mockStore.fetchSystemMetrics).toHaveBeenCalled()
    
    stopAutoRefresh()
    vi.advanceTimersByTime(60000)
    expect(mockStore.fetchSystemMetrics).toHaveBeenCalledTimes(1)
    
    vi.useRealTimers()
  })

  it('filters logs by level', async () => {
    const mockStore = {
      fetchSystemLogs: vi.fn()
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { filterLogs } = useMonitor()
    await filterLogs('error')

    expect(mockStore.fetchSystemLogs).toHaveBeenCalledWith(
      expect.objectContaining({ level: 'error' })
    )
  })

  it('sorts processes by resource usage', () => {
    const mockProcesses = [
      { pid: 1, cpu: 10, memory: 100 },
      { pid: 2, cpu: 20, memory: 200 }
    ]
    const mockStore = {
      processes: mockProcesses
    }
    vi.mocked(useMonitorStore).mockReturnValue(mockStore)

    const { sortProcesses } = useMonitor()
    const sortedByCpu = sortProcesses('cpu')
    const sortedByMemory = sortProcesses('memory')

    expect(sortedByCpu[0].cpu).toBe(20)
    expect(sortedByMemory[0].memory).toBe(200)
  })
})



