import request from '@/utils/request'
import type { NewsItem, NewsFilter, NewsCategory, NewsSource, NewsListResponse } from '@/types/news'

/**
 * 获取新闻列表
 */
export async function getNewsList(params: NewsFilter): Promise<NewsListResponse> {
  const { data } = await request.get('/news', { params })
  return data
}

/**
 * 获取新闻详情
 */
export async function getNewsDetail(id: string): Promise<NewsItem> {
  const { data } = await request.get(`/news/${id}`)
  return data
}

/**
 * 获取新闻分类列表
 */
export async function getCategories(): Promise<NewsCategory[]> {
  const { data } = await request.get('/news/categories')
  return data
}

/**
 * 获取新闻来源列表
 */
export async function getSources(): Promise<NewsSource[]> {
  const { data } = await request.get('/news/sources')
  return data
}

/**
 * 更新新闻
 */
export async function updateNews(id: string, data: Partial<NewsItem>): Promise<NewsItem> {
  const { data: responseData } = await request.put(`/news/${id}`, data)
  return responseData
}

/**
 * 删除新闻
 */
export async function deleteNews(id: string): Promise<void> {
  await request.delete(`/news/${id}`)
}

export default {
  getNewsList,
  getNewsDetail,
  getCategories,
  getSources,
  updateNews,
  deleteNews
} 