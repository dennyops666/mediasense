/**
 * 系统指标
 */
export interface SystemMetrics {
  cpu: {
    usage: number
    cores: number
    temperature: number
  }
  memory: {
    total: number
    used: number
    free: number
  }
  disk: {
    total: number
    used: number
    free: number
  }
  network: {
    rx_bytes: number
    tx_bytes: number
    connections: number
  }
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

export interface Alert {
  id: string
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'service'
  level: 'info' | 'warning' | 'critical'
  message: string
  timestamp: string
} 