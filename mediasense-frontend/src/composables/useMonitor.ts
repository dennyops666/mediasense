import { ref, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import type { SystemMetrics, SystemLog, ProcessInfo, Alert } from '@/types/api'

export function useMonitor() {
  const store = useMonitorStore()
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const resources = computed(() => {
    if (!store.metrics) {
      return {
        cpu: { usage: 0, cores: 0 },
        memory: { total: 0, used: 0, free: 0 },
        disk: { total: 0, used: 0, free: 0 },
        network: { upload: 0, download: 0, latency: 0 }
      }
    }
    return {
      cpu: {
        usage: store.metrics.cpu,
        cores: store.metrics.cpuCores
      },
      memory: {
        total: store.metrics.memoryTotal,
        used: store.metrics.memoryUsed,
        free: store.metrics.memoryFree
      },
      disk: {
        total: store.metrics.diskTotal,
        used: store.metrics.diskUsed,
        free: store.metrics.diskFree
      },
      network: {
        upload: store.metrics.networkUpload,
        download: store.metrics.networkDownload,
        latency: store.metrics.networkLatency
      }
    }
  })
  
  const logs = computed<SystemLog[]>(() => store.logs || [])
  const processes = computed<ProcessInfo[]>(() => store.processes || [])
  const alerts = computed<Alert[]>(() => store.alerts || [])

  // 获取系统指标
  const fetchMetrics = async () => {
    try {
      loading.value = true
      error.value = null
      await store.fetchSystemMetrics()
      return store.metrics
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取系统日志
  const fetchLogs = async () => {
    try {
      loading.value = true
      error.value = null
      await store.fetchSystemLogs({ page: 1, pageSize: 10 })
      return store.logs
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取进程列表
  const fetchProcesses = async () => {
    try {
      loading.value = true
      error.value = null
      await store.fetchProcessList()
      return store.processes
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取告警列表
  const fetchAlerts = async () => {
    try {
      loading.value = true
      error.value = null
      await store.fetchAlerts()
      return store.alerts
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 确认告警
  const acknowledgeAlert = async (alertId: string) => {
    try {
      loading.value = true
      error.value = null
      await store.handleAcknowledgeAlert(alertId)
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除告警
  const deleteAlert = async (alertId: string) => {
    try {
      loading.value = true
      error.value = null
      await store.deleteAlert(alertId)
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 清除所有告警
  const clearAllAlerts = async () => {
    try {
      loading.value = true
      error.value = null
      await store.clearAllAlerts()
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 开始自动更新
  const startAutoUpdate = () => {
    store.startAutoUpdate()
  }

  // 停止自动更新
  const stopAutoUpdate = () => {
    store.stopAutoUpdate()
  }

  // 导出监控数据
  const exportData = async () => {
    try {
      loading.value = true
      error.value = null
      const result = await store.exportMonitoringData()
      return result
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    resources,
    logs,
    processes,
    alerts,
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
    exportData
  }
} 