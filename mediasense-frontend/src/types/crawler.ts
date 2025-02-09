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
  type: string
  targetUrl: string
  method: 'GET' | 'POST'
  body?: string
  headers: Array<{
    key: string
    value: string
  }>
  selectors: Array<{
    field: string
    selector: string
    type: 'css' | 'xpath'
    attr?: string
  }>
  timeout: number
  retries: number
  concurrency: number
  proxy?: string
  userAgent: string
}

/**
 * 爬虫任务
 */
export interface CrawlerTask {
  id: string
  name: string
  type: string
  schedule: string
  config: Record<string, any>
  status: 'running' | 'stopped' | 'error'
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

export type TaskStatus = 'running' | 'stopped' | 'error'

export interface CrawlerData {
  id: string
  taskId: string
  title: string
  content: string
  url: string
  source: string
  category: string
  publishTime: string
  crawlTime: string
  rawData: Record<string, any>
}

export interface TaskQueryParams {
  page?: number
  pageSize?: number
  keyword?: string
  status?: TaskStatus
}

export interface DataQueryParams {
  taskId?: string
  startTime?: string
  endTime?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
} 