// 搜索参数接口
export interface SearchParams {
  keyword: string
  category: string
  source: string
  dateRange: [Date, Date] | null
  sortBy: 'relevance' | 'date'
  order: 'asc' | 'desc'
  page: number
  pageSize: number
}

// 搜索结果接口
export interface SearchResults {
  total: number
  items: NewsItem[]
  facets: {
    categories: Record<string, number>
    sources: Record<string, number>
  }
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

// 搜索历史项目接口
export interface SearchHistoryItem {
  keyword: string
  timestamp: string
} 