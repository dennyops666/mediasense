// 搜索参数接口
export interface SearchParams {
  keyword: string
  type?: string
  date?: string | null
  page: number
  pageSize: number
}

// 搜索结果接口
export interface SearchResult {
  id: string
  title: string
  content: string
  source: string
  publishTime: string
  relevanceScore: number
}

// 搜索响应接口
export interface SearchResponse {
  items: SearchResult[]
  total: number
}

// 搜索状态接口
export interface SearchState {
  keyword: string
  type: string
  date: string | null
  currentPage: number
  pageSize: number
  results: SearchResult[]
  total: number
  loading: boolean
  error: string | null
  suggestions: string[]
  searchHistory: string[]
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