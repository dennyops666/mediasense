import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SystemMetrics, SystemLog, ProcessInfo, DiskUsage } from '@/types/api'
import * as monitorApi from '@/api/monitor'
import { ElMessage } from 'element-plus'
import type { ServiceStatus, Alert } from '@/types/monitor'

interface MetricsHistory {
  timestamps: string[]
  values: number[]
}

export const useMonitorStore = defineStore('monitor', () => {
  // 状态
  const metrics = ref<SystemMetrics | null>(null)
  const logs = ref<SystemLog[]>([])
  const totalLogs = ref(0)
  const processes = ref<ProcessInfo[]>([])
  const diskUsage = ref<DiskUsage[]>([])
  const services = ref<ServiceStatus[]>([])
  const alerts = ref<Alert[]>([])
  const loading = ref(false)
  const metricsHistory = ref<MetricsHistory>({
    timestamps: [],
    values: []
  })

  // 获取系统指标
  const fetchSystemMetrics = async () => {
    try {
      loading.value = true
      const data = await monitorApi.getSystemMetrics()
      metrics.value = data
    } catch (error) {
      metrics.value = null
      ElMessage.error('获取系统指标失败')
    } finally {
      loading.value = false
    }
  }

  // 获取系统日志
  const fetchSystemLogs = async (params: { page: number; pageSize: number; level?: string }) => {
    try {
      loading.value = true
      const data = await monitorApi.getSystemLogs(params)
      logs.value = data.items
      totalLogs.value = data.total
    } catch (error) {
      logs.value = []
      totalLogs.value = 0
      ElMessage.error('获取系统日志失败')
    } finally {
      loading.value = false
    }
  }

  // 获取指标历史
  const fetchMetricsHistory = async (params: { startTime: string; endTime: string; type: string }) => {
    try {
      loading.value = true
      const data = await monitorApi.getMetricsHistory(params)
      metricsHistory.value = data
    } catch (error) {
      metricsHistory.value = { timestamps: [], values: [] }
      ElMessage.error('获取指标历史失败')
    } finally {
      loading.value = false
    }
  }

  // 获取进程列表
  const fetchProcessList = async () => {
    try {
      loading.value = true
      const data = await monitorApi.getProcessList()
      processes.value = data
    } catch (error) {
      processes.value = []
      ElMessage.error('获取进程列表失败')
    } finally {
      loading.value = false
    }
  }

  // 获取磁盘使用情况
  const fetchDiskUsage = async () => {
    try {
      loading.value = true
      const data = await monitorApi.getDiskUsage()
      diskUsage.value = data
    } catch (error) {
      diskUsage.value = []
      ElMessage.error('获取磁盘使用情况失败')
    } finally {
      loading.value = false
    }
  }

  // 获取服务状态
  const fetchServiceStatus = async () => {
    try {
      loading.value = true
      const data = await monitorApi.getServiceStatus()
      services.value = data
    } catch (error) {
      services.value = []
      ElMessage.error('获取服务状态失败')
    } finally {
      loading.value = false
    }
  }

  // 获取告警信息
  const fetchAlerts = async () => {
    try {
      loading.value = true
      const data = await monitorApi.getAlerts()
      alerts.value = data
    } catch (error) {
      alerts.value = []
      ElMessage.error('获取告警信息失败')
    } finally {
      loading.value = false
    }
  }

  // 重启服务
  const handleRestartService = async (serviceName: string) => {
    try {
      loading.value = true
      const data = await monitorApi.restartService(serviceName)
      await fetchServiceStatus()
      return data
    } catch (error) {
      ElMessage.error('重启服务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 确认告警
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      loading.value = true
      await monitorApi.acknowledgeAlert(alertId)
      await fetchAlerts()
    } catch (error) {
      ElMessage.error('确认告警失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    metrics,
    logs,
    totalLogs,
    processes,
    diskUsage,
    services,
    alerts,
    loading,
    metricsHistory,
    fetchSystemMetrics,
    fetchSystemLogs,
    fetchMetricsHistory,
    fetchProcessList,
    fetchDiskUsage,
    fetchServiceStatus,
    fetchAlerts,
    handleRestartService,
    handleAcknowledgeAlert
  }
}) 