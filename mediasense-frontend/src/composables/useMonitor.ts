import { ref, onMounted, onUnmounted } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import type { SystemMetrics, Alert } from '@/types/monitor'

export function useMonitor() {
  const store = useMonitorStore()
  const updateInterval = ref<number>()
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取系统指标
  const fetchMetrics = async () => {
    try {
      loading.value = true
      await store.fetchSystemMetrics()
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统指标失败'
    } finally {
      loading.value = false
    }
  }

  // 获取系统日志
  const fetchLogs = async (params: {
    page: number
    pageSize: number
    level?: string
  }) => {
    try {
      loading.value = true
      await store.fetchSystemLogs(params)
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统日志失败'
    } finally {
      loading.value = false
    }
  }

  // 获取进程列表
  const fetchProcesses = async () => {
    try {
      loading.value = true
      await store.fetchProcessList()
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取进程列表失败'
    } finally {
      loading.value = false
    }
  }

  // 获取告警列表
  const fetchAlerts = async (params: {
    page: number
    pageSize: number
    level?: string
  }) => {
    try {
      loading.value = true
      await store.fetchAlerts(params)
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取告警列表失败'
    } finally {
      loading.value = false
    }
  }

  // 确认告警
  const acknowledgeAlert = async (alertId: string) => {
    try {
      loading.value = true
      await store.acknowledgeAlert(alertId)
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '确认告警失败'
    } finally {
      loading.value = false
    }
  }

  // 删除告警
  const deleteAlert = async (alertId: string) => {
    try {
      loading.value = true
      await store.deleteAlert(alertId)
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除告警失败'
    } finally {
      loading.value = false
    }
  }

  // 清除所有告警
  const clearAllAlerts = async () => {
    try {
      loading.value = true
      await store.clearAllAlerts()
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清除告警失败'
    } finally {
      loading.value = false
    }
  }

  // 开始自动更新
  const startAutoUpdate = (interval = 5000) => {
    stopAutoUpdate()
    updateInterval.value = window.setInterval(() => {
      fetchMetrics()
    }, interval)
  }

  // 停止自动更新
  const stopAutoUpdate = () => {
    if (updateInterval.value) {
      clearInterval(updateInterval.value)
      updateInterval.value = undefined
    }
  }

  // 导出监控数据
  const exportMonitorData = () => {
    return store.exportMonitoringData()
  }

  // 生命周期钩子
  onMounted(() => {
    fetchMetrics()
    startAutoUpdate()
  })

  onUnmounted(() => {
    stopAutoUpdate()
  })

  return {
    // 状态
    metrics: store.metrics,
    logs: store.logs,
    processes: store.processes,
    alerts: store.alerts,
    loading,
    error,

    // 方法
    fetchMetrics,
    fetchLogs,
    fetchProcesses,
    fetchAlerts,
    acknowledgeAlert,
    deleteAlert,
    clearAllAlerts,
    startAutoUpdate,
    stopAutoUpdate,
    exportMonitorData
  }
} 