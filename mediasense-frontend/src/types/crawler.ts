/**
 * 爬虫配置
 */
export interface CrawlerConfig {
  id: string
  name: string
  description?: string
  type: 'web' | 'rss' | 'api'
  url: string
  method: 'GET' | 'POST'
  headers?: Record<string, string>
  body?: string
  selectors: {
    title: string
    content: string
    date?: string
    author?: string
    category?: string
    tags?: string
  }
  schedule?: string
  enabled: boolean
  timeout?: number
  retries?: number
  concurrency?: number
  proxy?: string
  userAgent?: string
  createdAt?: string
  updatedAt?: string
}

/**
 * 爬虫任务
 */
export interface CrawlerTask {
  id: string
  name: string
  type: 'web' | 'rss' | 'api'
  schedule: string
  config: Record<string, any>
  status: TaskStatus
  lastRunTime: string
  count: number
  configId: string
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
export interface TaskLog {
  id: string
  taskId: string
  level: LogLevel
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
  stoppedTasks: number
  errorTasks: number
  totalItems: number
  successRate: number
}

export type TaskStatus = 'running' | 'stopped' | 'error'
export type LogLevel = 'info' | 'warning' | 'error'

export interface CrawlerData {
  id: string
  taskId: string
  title: string
  content: string
  url: string
  source: string
  category?: string
  tags?: string[]
  author?: string
  publishTime?: string
  crawlTime: string
  rawData?: Record<string, any>
}

export interface TaskQueryParams {
  page?: number
  pageSize?: number
  keyword?: string
  status?: TaskStatus
  type?: string
  startTime?: string
  endTime?: string
}

export interface DataQueryParams {
  taskId?: string
  keyword?: string
  category?: string
  startTime?: string
  endTime?: string
  page?: number
  pageSize?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface TaskLogQueryParams {
  taskId: string
  level?: LogLevel
  keyword?: string
  startTime?: string
  endTime?: string
  page?: number
  pageSize?: number
} 