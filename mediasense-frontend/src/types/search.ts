// 搜索参数接口
export interface SearchParams {
  keyword: string
  type?: string
  category?: string
  source?: string
  date?: string
  dateRange?: [string, string] | null
  sortBy?: 'relevance' | 'date'
  order?: 'asc' | 'desc'
  page?: number
  pageSize?: number
}

// 搜索结果接口
export interface SearchResult {
  id: number | string
  title: string
  content: string
  summary?: string
  source: string
  author?: string
  publishTime: string
  category?: string
  tags?: string[]
  url?: string
  score: number
}

export interface SearchResponse {
  items: SearchResult[]
  total: number
  facets?: {
    categories?: Record<string, number>
    sources?: Record<string, number>
  }
}

// 搜索建议接口
export interface SearchSuggestion {
  text: string
  type?: string
  count?: number
}

// 搜索历史项目接口
export interface SearchHistory {
  keyword: string
  timestamp: string
  type?: string
}

// 新闻项目接口
export interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  source: string
  author: string
  publishTime: string
  category: string
  tags: string[]
  url: string
  createdAt: string
  updatedAt: string
}

// 热门搜索词接口
export interface HotKeyword {
  keyword: string
  count: number
} 