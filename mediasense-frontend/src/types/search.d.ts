export interface SearchParams {
  keyword: string
  type: string
  page: number
  pageSize: number
  date: string
  sort: string
}

export interface SearchResult {
  id: number
  title: string
  [key: string]: any
} 