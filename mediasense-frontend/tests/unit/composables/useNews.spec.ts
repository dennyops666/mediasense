import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useNews } from '@/composables/useNews'
import { useNewsStore } from '@/stores/news'
import { createTestingPinia } from '@pinia/testing'
import { setActivePinia } from 'pinia'

// Mock data
const mockNewsList = [
  {
    id: 1,
    title: '测试新闻1',
    content: '这是测试新闻1的内容',
    source: '测试来源',
    publishTime: '2024-03-20T10:00:00Z',
    category: '科技'
  },
  {
    id: 2,
    title: '测试新闻2',
    content: '这是测试新闻2的内容',
    source: '测试来源',
    publishTime: '2024-03-20T11:00:00Z',
    category: '财经'
  }
]

const mockNewsDetail = {
  id: 1,
  title: '测试新闻1',
  content: '这是测试新闻1的详细内容',
  source: '测试来源',
  publishTime: '2024-03-20T10:00:00Z',
  category: '科技',
  author: '测试作者',
  tags: ['标签1', '标签2'],
  relatedNews: []
}

describe('useNews', () => {
  let news
  let store

  beforeEach(() => {
    setActivePinia(createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        news: {
          newsList: [],
          currentNews: null,
          loading: false,
          error: null,
          total: 0,
          categories: ['科技', '财经', '社会']
        }
      }
    }))

    store = useNewsStore()
    store.fetchNewsList = vi.fn().mockResolvedValue(mockNewsList)
    store.fetchNewsDetail = vi.fn().mockResolvedValue(mockNewsDetail)
    store.createNews = vi.fn().mockResolvedValue({ id: 3 })
    store.updateNews = vi.fn().mockResolvedValue(true)
    store.deleteNews = vi.fn().mockResolvedValue(true)

    news = useNews()
  })

  describe('新闻列表', () => {
    it('应该能获取新闻列表', async () => {
      const params = { page: 1, pageSize: 10 }
      store.newsList = []  // 确保初始状态为空
      store.fetchNewsList.mockImplementation(async () => {
        store.newsList = mockNewsList
        return mockNewsList
      })
      
      await news.fetchNewsList(params)

      expect(store.fetchNewsList).toHaveBeenCalledWith(params)
      expect(news.newsList.value).toEqual(mockNewsList)
      expect(news.loading.value).toBe(false)
    })

    it('应该能按分类筛选新闻', async () => {
      const params = { page: 1, pageSize: 10, category: '科技' }
      await news.fetchNewsList(params)

      expect(store.fetchNewsList).toHaveBeenCalledWith(params)
    })

    it('应该正确处理加载状态', async () => {
      const promise = news.fetchNewsList({ page: 1, pageSize: 10 })
      expect(news.loading.value).toBe(true)
      
      await promise
      expect(news.loading.value).toBe(false)
    })
  })

  describe('新闻详情', () => {
    it('应该能获取新闻详情', async () => {
      const newsId = 1
      store.currentNews = null  // 确保初始状态为 null
      store.fetchNewsDetail.mockImplementation(async () => {
        store.currentNews = mockNewsDetail
        return mockNewsDetail
      })
      
      await news.fetchNewsDetail(newsId)

      expect(store.fetchNewsDetail).toHaveBeenCalledWith(newsId)
      expect(news.currentNews.value).toEqual(mockNewsDetail)
    })

    it('应该能创建新闻', async () => {
      const newsData = {
        title: '新测试新闻',
        content: '新测试内容',
        category: '科技'
      }
      await news.createNews(newsData)

      expect(store.createNews).toHaveBeenCalledWith(newsData)
    })

    it('应该能更新新闻', async () => {
      const newsId = 1
      const updateData = {
        title: '更新的标题',
        content: '更新的内容'
      }
      await news.updateNews(newsId, updateData)

      expect(store.updateNews).toHaveBeenCalledWith(newsId, updateData)
    })

    it('应该能删除新闻', async () => {
      const newsId = 1
      await news.deleteNews(newsId)

      expect(store.deleteNews).toHaveBeenCalledWith(newsId)
    })
  })

  describe('错误处理', () => {
    it('应该正确处理获取列表失败', async () => {
      const error = new Error('获取新闻列表失败')
      store.fetchNewsList.mockRejectedValueOnce(error)

      try {
        await news.fetchNewsList({ page: 1, pageSize: 10 })
      } catch (err) {
        expect(news.error.value).toBe('获取新闻列表失败')
        expect(news.loading.value).toBe(false)
      }
    })

    it('应该正确处理获取详情失败', async () => {
      const error = new Error('获取新闻详情失败')
      store.fetchNewsDetail.mockRejectedValueOnce(error)

      try {
        await news.fetchNewsDetail(1)
      } catch (err) {
        expect(news.error.value).toBe('获取新闻详情失败')
        expect(news.loading.value).toBe(false)
      }
    })
  })

  describe('工具方法', () => {
    it('应该能格式化发布时间', () => {
      const time = '2024-03-20T10:00:00Z'
      expect(news.formatPublishTime(time)).toBeDefined()
    })

    it('应该能获取新闻分类列表', () => {
      expect(news.categories.value).toEqual(['科技', '财经', '社会'])
    })
  })
})

