/**
 * 新闻项
 */
export interface NewsItem {
  id: string
  title: string
  content: string
  summary?: string
  category: string
  source: string
  author?: string
  publishTime: string
  status: 'draft' | 'published' | 'archived'
  tags?: string[]
  url?: string
  createdAt?: string
  updatedAt?: string
}

/**
 * 新闻分类
 */
export interface NewsCategory {
  id: string
  name: string
  description?: string
}

/**
 * 新闻来源
 */
export interface NewsSource {
  id: string
  name: string
  url?: string
  description?: string
}

/**
 * 新闻过滤条件
 */
export interface NewsFilter {
  page: number
  pageSize: number
  keyword: string
  category: string
  source: string
  startDate: string
  endDate: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
}

/**
 * 新闻列表响应
 */
export interface NewsListResponse {
  list: NewsItem[]
  total: number
} 