import { defineStore } from 'pinia'
import * as newsApi from '@/api/news'
import type { NewsItem, NewsFilter } from '@/types/news'

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [] as NewsItem[],
    currentNews: null as NewsItem | null,
    categories: [] as string[],
    sources: [] as string[],
    total: 0,
    loading: false,
    error: null as string | null,
    filter: {
      page: 1,
      pageSize: 10,
      keyword: '',
      category: '',
      source: '',
      startDate: '',
      endDate: '',
      sortBy: 'publishTime',
      sortOrder: 'desc'
    } as NewsFilter
  }),

  actions: {
    setError(error: string | null) {
      this.error = error
    },

    clearError() {
      this.error = null
    },

    async fetchNewsList(params?: Partial<NewsFilter>) {
      try {
        this.loading = true
        const filter = { ...this.filter, ...params }
        const { list, total } = await newsApi.getNewsList(filter)
        this.newsList = list
        this.total = total
        this.filter = filter
      } catch (error) {
        console.error('获取新闻列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchNewsDetail(id: string) {
      try {
        this.loading = true
        this.clearError()
        const news = await newsApi.getNewsDetail(id)
        if (!news) {
          this.setError('新闻不存在')
          return null
        }
        this.currentNews = news
        return news
      } catch (error) {
        console.error('获取新闻详情失败:', error)
        this.setError('获取新闻详情失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCategories() {
      try {
        const categories = await newsApi.getCategories()
        this.categories = categories.map(c => c.name)
        return categories
      } catch (error) {
        console.error('获取新闻分类失败:', error)
        throw error
      }
    },

    async fetchSources() {
      try {
        const sources = await newsApi.getSources()
        this.sources = sources.map(s => s.name)
        return sources
      } catch (error) {
        console.error('获取新闻来源失败:', error)
        throw error
      }
    },

    async updateNews(id: string, data: Partial<NewsItem>) {
      try {
        const updated = await newsApi.updateNews(id, data)
        const index = this.newsList.findIndex(item => item.id === id)
        if (index > -1) {
          this.newsList[index] = updated
        }
        if (this.currentNews?.id === id) {
          this.currentNews = updated
        }
        return updated
      } catch (error) {
        console.error('更新新闻失败:', error)
        throw error
      }
    },

    async deleteNews(id: string) {
      try {
        this.clearError()
        await newsApi.deleteNews(id)
        this.newsList = this.newsList.filter(item => item.id !== id)
        if (this.currentNews?.id === id) {
          this.currentNews = null
        }
      } catch (error) {
        console.error('删除新闻失败:', error)
        this.setError('删除新闻失败')
        throw error
      }
    },

    async applyFilter(filter: Partial<NewsFilter>) {
      await this.fetchNewsList(filter)
    },

    resetFilter() {
      this.filter = {
        page: 1,
        pageSize: 10,
        keyword: '',
        category: '',
        source: '',
        startDate: '',
        endDate: '',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      }
    }
  }
}) 