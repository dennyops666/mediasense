/**
 * 爬虫配置
 */
export interface CrawlerConfig {
  id: string
  name: string
  description?: string
  url: string
  selector: {
    title: string
    content: string
    date?: string
    author?: string
    category?: string
    tags?: string
  }
  schedule?: string
  enabled: boolean
  createdAt?: string
  updatedAt?: string
}

/**
 * 爬虫任务
 */
export interface CrawlerTask {
  id: string
  configId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
  totalItems: number
  successItems: number
  failedItems: number
  error?: string
  createdAt: string
  updatedAt: string
}

/**
 * 爬虫任务日志
 */
export interface CrawlerTaskLog {
  id: string
  taskId: string
  level: 'info' | 'warning' | 'error'
  message: string
  timestamp: string
}

/**
 * 爬虫统计信息
 */
export interface CrawlerStats {
  totalConfigs: number
  enabledConfigs: number
  totalTasks: number
  runningTasks: number
  completedTasks: number
  failedTasks: number
  totalItems: number
  successRate: number
} 