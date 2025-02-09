/**
 * 新闻项
 */
export interface News {
  id: string
  title: string
  content: string
  category: string
  publishTime: string
  author: string
  views: number
  summary?: string
  tags?: string[]
  source?: string
  imageUrl?: string
}

/**
 * 新闻分类
 */
export interface NewsCategory {
  id: string
  name: string
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
  items: News[]
  total: number
  page: number
  pageSize: number
}

export interface NewsSearchParams {
  page: number
  pageSize: number
  category?: string
  keyword?: string
  startDate?: string
  endDate?: string
  sortBy?: 'publishTime' | 'views'
  sortOrder?: 'asc' | 'desc'
} 