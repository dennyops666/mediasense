// 认证相关类型
export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm extends LoginForm {
  email: string
}

export interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'admin'
  createdAt: string
}

export interface AuthResponse {
  token: string
  user: User
}

// 新闻相关类型
export interface News {
  id: string
  title: string
  content: string
  summary: string
  source: string
  author: string
  publishTime: string
  status: 'published' | 'draft'
  category: string
  tags: string[]
  url: string
  createdAt: string
  updatedAt: string
}

export interface NewsFilter {
  category?: string
  source?: string
  dateRange?: [string, string]
  keyword?: string
  page: number
  pageSize: number
}

export interface NewsResponse {
  total: number
  items: News[]
}

// 搜索相关类型
export interface SearchParams extends NewsFilter {
  sortBy?: 'relevance' | 'date'
  order?: 'asc' | 'desc'
}

export interface SearchResponse {
  total: number
  items: News[]
  facets: {
    categories: { [key: string]: number }
    sources: { [key: string]: number }
  }
}

// 监控相关类型
export interface SystemMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  processCount: number
  lastUpdate: string
  networkIo: {
    input: number  // 字节/秒
    output: number // 字节/秒
  }
}

export interface SystemLog {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error'
  module: string
  message: string
}

// 爬虫配置相关类型
export interface CrawlerConfig {
  id: string
  name: string
  siteName: string
  siteUrl: string
  frequency: number // 爬取频率（分钟）
  enabled: boolean
  lastRunTime?: string
  createdAt: string
  updatedAt: string
}

// AI 服务相关类型
export interface SentimentAnalysis {
  text: string
  sentiment: 'positive' | 'negative' | 'neutral'
  score: number
  keywords: string[]
}

export interface TextSummary {
  originalText: string
  summary: string
  keyPoints: string[]
  wordCount: number
}

export interface TopicAnalysis {
  text: string
  topics: Array<{
    name: string
    confidence: number
    keywords: string[]
  }>
}

export interface TrendAnalysis {
  keyword: string
  period: string
  trends: Array<{
    date: string
    frequency: number
    sentiment: number
  }>
  relatedTopics: Array<{
    topic: string
    correlation: number
  }>
}

export interface AIAnalysisRequest {
  text?: string
  keyword?: string
  timeRange?: [string, string]
  type: 'sentiment' | 'summary' | 'topic' | 'trend'
  options?: {
    maxLength?: number
    language?: string
    includeKeywords?: boolean
  }
}

export interface AIAnalysisResponse {
  type: 'sentiment' | 'summary' | 'topic' | 'trend'
  result: SentimentAnalysis | TextSummary | TopicAnalysis | TrendAnalysis
  processingTime: number
  timestamp: string
} 