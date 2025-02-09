/**
 * 系统指标
 */
export interface SystemMetrics {
  cpu?: {
    usage: number
    temperature: number
    cores: number[]
  }
  memory?: {
    total: number
    used: number
    free: number
    usagePercentage: number
  }
  disk?: {
    total: number
    used: number
    free: number
    usagePercentage: number
    readSpeed: number
    writeSpeed: number
  }
  network?: {
    upload: number
    download: number
    latency: number
  }
  timestamp: string
}

/**
 * 系统日志
 */
export interface SystemLog {
  id: string
  level: 'info' | 'warning' | 'error'
  message: string
  source: string
  timestamp: string
  metadata?: Record<string, any>
}

/**
 * 历史指标数据
 */
export interface MetricsHistory {
  metric: string
  value: number
  timestamp: string
}

/**
 * 进程信息
 */
export interface ProcessInfo {
  pid: number
  name: string
  command: string
  cpu: number
  memory: number
  status: string
  user: string
  startTime: string
  uptime: number
}

/**
 * 磁盘使用情况
 */
export interface DiskUsage {
  device: string
  mountPoint: string
  fsType: string
  total: number
  used: number
  free: number
  usage: number
}

export interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'warning'
  uptime: string
  lastCheck: string
}

export const AlertLevel = {
  CRITICAL: 'critical',
  WARNING: 'warning',
  INFO: 'info'
} as const

export type AlertLevelType = typeof AlertLevel[keyof typeof AlertLevel]

export interface Alert {
  id: string
  message: string
  level: AlertLevelType
  timestamp: string
  source: string
  acknowledged?: {
    time: string
    by: string
  }
}

export interface MonitoringData {
  metrics: SystemMetrics
  activeAlerts: Alert[]
  alertHistory: Alert[]
  timestamp: string
  version: string
} 