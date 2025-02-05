// 新闻类型定义
export interface News {
  id: string
  title: string
  content: string
  summary: string
  source: string
  author: string
  publishTime: string
  status: 'draft' | 'published' | 'archived'
  category: string
  tags: string[]
  url: string
  createdAt: string
  updatedAt: string
}

// 新闻过滤器类型
export interface NewsFilter {
  category?: string
  source?: string
  dateRange?: [string, string] | null
  keyword?: string
  page?: number
  pageSize?: number
}

// 用户类型定义
export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'user' | 'guest'
  createdAt: string
}

// 认证响应类型
export interface AuthResponse {
  token: string
  user: User
}

// 爬虫配置类型
export interface CrawlerConfig {
  id: string
  name: string
  siteName: string
  siteUrl: string
  frequency: string
  status: string
  configType: string
  useProxy: boolean
  isEnabled: boolean
  lastRun: string | null
  nextRun: string | null
  errorCount: number
  lastError: string | null
}

// 系统监控指标类型
export interface SystemMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkIo: {
    input: number
    output: number
  }
  processCount: number
  errorCount: number
  collectionTime: string
} 