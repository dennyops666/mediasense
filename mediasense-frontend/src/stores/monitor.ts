import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as monitorApi from '@/api/monitor'
import type { SystemMetrics, SystemLog, ProcessInfo, Alert } from '@/types/monitor'

export const useMonitorStore = defineStore('monitor', () => {
  const metrics = ref<SystemMetrics>({
    cpu: { usage: 0, cores: 0, temperature: 0 },
    memory: { total: '0 GB', used: '0 GB', usagePercentage: 0 },
    disk: { total: '0 GB', used: '0 GB', usagePercentage: 0 },
    network: { upload: '0 MB/s', download: '0 MB/s', latency: 0 }
  })
  const logs = ref<SystemLog[]>([])
  const processes = ref<ProcessInfo[]>([])
  const alerts = ref<Alert[]>([])
  const error = ref<string | null>(null)
  const loading = ref(false)
  const isMonitoring = ref(false)
  const isExporting = ref(false)
  const monitoringInterval = ref(5000)
  let monitoringTimer: number | null = null

  // 获取系统指标
  const fetchSystemMetrics = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await monitorApi.getSystemMetrics()
      metrics.value = response.data
      checkAlerts()
    } catch (err) {
      error.value = '获取失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取系统日志
  const fetchSystemLogs = async (params: { page: number; pageSize: number }) => {
    try {
      loading.value = true
      error.value = null
      const response = await monitorApi.getSystemLogs(params)
      logs.value = response.data.items
      return response.data.items
    } catch (err) {
      error.value = '获取失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取进程列表
  const fetchProcessList = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await monitorApi.getProcessList()
      processes.value = response.data
      return response.data
    } catch (err) {
      error.value = '获取失败'
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
      const response = await monitorApi.getAlerts()
      alerts.value = response.data
      return response.data
    } catch (err) {
      error.value = '获取失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 确认告警
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      loading.value = true
      error.value = null
      await monitorApi.acknowledgeAlert(alertId)
      await fetchAlerts()
    } catch (err) {
      error.value = '确认失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 检查告警
  const checkAlerts = () => {
    if (!metrics.value) return

    const { cpu, memory, disk } = metrics.value
    const newAlerts: Alert[] = []

    if (cpu?.usage && cpu.usage > 80) {
      newAlerts.push({
        id: Date.now().toString(),
        message: 'CPU 使用率过高',
        level: 'critical',
        timestamp: new Date().toISOString(),
        source: 'system'
      })
    }

    if (memory?.usagePercentage && memory.usagePercentage > 80) {
      newAlerts.push({
        id: (Date.now() + 1).toString(),
        message: '内存使用率过高',
        level: 'warning',
        timestamp: new Date().toISOString(),
        source: 'system'
      })
    }

    if (disk?.usagePercentage && disk.usagePercentage > 90) {
      newAlerts.push({
        id: (Date.now() + 2).toString(),
        message: '磁盘使用率过高',
        level: 'critical',
        timestamp: new Date().toISOString(),
        source: 'system'
      })
    }

    alerts.value = [...alerts.value, ...newAlerts]
  }

  // 开始监控
  const startMonitoring = async (interval: number = 5000) => {
    try {
      if (monitoringTimer) {
        clearInterval(monitoringTimer)
      }
      
      await fetchSystemMetrics()
      monitoringInterval.value = interval
      monitoringTimer = window.setInterval(fetchSystemMetrics, interval)
      isMonitoring.value = true
    } catch (err) {
      error.value = '启动监控失败'
      throw err
    }
  }

  // 停止监控
  const stopMonitoring = () => {
    if (monitoringTimer) {
      clearInterval(monitoringTimer)
      monitoringTimer = null
    }
    isMonitoring.value = false
  }

  // 导出监控数据
  const exportMonitoringData = async () => {
    try {
      isExporting.value = true
      error.value = null
      
      if (!metrics.value) {
        throw new Error('没有可导出的数据')
      }

      const data = {
        metrics: metrics.value,
        alerts: alerts.value,
        timestamp: new Date().toISOString(),
        version: '1.0'
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `monitoring-data-${new Date().toISOString()}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      URL.revokeObjectURL(url)
      return blob
    } catch (err) {
      error.value = '导出失败'
      throw err
    } finally {
      isExporting.value = false
    }
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    metrics,
    logs,
    processes,
    alerts,
    error,
    loading,
    isMonitoring,
    isExporting,
    monitoringInterval,

    // 方法
    fetchSystemMetrics,
    fetchSystemLogs,
    fetchProcessList,
    fetchAlerts,
    handleAcknowledgeAlert,
    startMonitoring,
    stopMonitoring,
    exportMonitoringData,
    clearError
  }
})