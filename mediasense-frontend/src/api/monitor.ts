import request from '@/utils/request'
import type { SystemMetrics, SystemLog, ProcessInfo, DiskUsage, ServiceStatus, Alert } from '@/types/api'

interface LogsParams {
  page: number
  pageSize: number
  level?: 'info' | 'warning' | 'error'
}

interface LogsResponse {
  total: number
  items: SystemLog[]
}

interface MetricsHistoryParams {
  startTime: string
  endTime: string
  type: string
}

interface MetricsHistoryResponse {
  timestamps: string[]
  values: number[]
}

export const getSystemMetrics = async (): Promise<SystemMetrics> => {
  const response = await request.get('/api/monitor/metrics')
  return response.data
}

export const getSystemLogs = async (params: LogsParams): Promise<LogsResponse> => {
  const response = await request.get('/api/monitor/logs', { params })
  return response.data
}

export const getMetricsHistory = async (params: MetricsHistoryParams): Promise<MetricsHistoryResponse> => {
  const response = await request.get('/api/monitor/metrics/history', { params })
  return response.data
}

export const getProcessList = async (): Promise<ProcessInfo[]> => {
  const response = await request.get('/api/monitor/processes')
  return response.data
}

export const getDiskUsage = async (): Promise<DiskUsage[]> => {
  const response = await request.get('/api/monitor/disk')
  return response.data
}

export const getServiceStatus = async (): Promise<ServiceStatus[]> => {
  const response = await request.get('/api/monitor/services')
  return response.data
}

export const getAlerts = async (): Promise<Alert[]> => {
  const response = await request.get('/api/monitor/alerts')
  return response.data
}

export const restartService = async (serviceName: string): Promise<{ success: boolean; message: string }> => {
  const response = await request.post('/api/monitor/services/restart', { serviceName })
  return response.data
}

export const acknowledgeAlert = async (alertId: string): Promise<{ success: boolean; message: string }> => {
  const response = await request.post('/api/monitor/alerts/acknowledge', { alertId })
  return response.data
}

export default {
  getSystemMetrics,
  getSystemLogs,
  getMetricsHistory,
  getProcessList,
  getDiskUsage,
  getServiceStatus,
  getAlerts,
  restartService,
  acknowledgeAlert
} 