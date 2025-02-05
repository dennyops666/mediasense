import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAIStore } from '@/stores/ai'
import * as aiApi from '@/api/ai'

vi.mock('@/api/ai')
vi.mock('element-plus')

describe('AI Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('analyzeSentiment', () => {
    it('应该正确处理情感分析请求', async () => {
      const store = useAIStore()
      const mockResponse = {
        sentiment: 'positive',
        score: 0.85,
        keywords: ['优秀', '出色', '满意']
      }

      vi.mocked(aiApi.analyzeSentiment).mockResolvedValueOnce(mockResponse)

      const text = '这是测试文本'
      const result = await store.analyzeSentiment(text)

      expect(aiApi.analyzeSentiment).toHaveBeenCalledWith(text)
      expect(result).toEqual(mockResponse)
      expect(store.sentimentResult).toEqual(mockResponse)
      expect(store.loading).toBe(false)
    })

    it('应该处理情感分析错误', async () => {
      const store = useAIStore()
      const error = new Error('API错误')

      vi.mocked(aiApi.analyzeSentiment).mockRejectedValueOnce(error)

      const text = '这是测试文本'
      await expect(store.analyzeSentiment(text)).rejects.toThrow(error)
      expect(store.loading).toBe(false)
    })
  })

  describe('generateSummary', () => {
    it('应该正确处理文本摘要请求', async () => {
      const store = useAIStore()
      const mockResponse = {
        originalText: '这是原始文本',
        summary: '这是摘要',
        keyPoints: ['要点1', '要点2'],
        wordCount: 100
      }

      vi.mocked(aiApi.generateSummary).mockResolvedValueOnce(mockResponse)

      const text = '这是测试文本'
      const maxLength = 200
      const result = await store.generateSummary(text, maxLength)

      expect(aiApi.generateSummary).toHaveBeenCalledWith(text, maxLength)
      expect(result).toEqual(mockResponse)
      expect(store.summaryResult).toEqual(mockResponse)
      expect(store.loading).toBe(false)
    })
  })

  describe('analyzeTopics', () => {
    it('应该正确处理主题分析请求', async () => {
      const store = useAIStore()
      const mockResponse = {
        text: '这是测试文本',
        topics: [
          {
            name: '主题1',
            confidence: 0.9,
            keywords: ['关键词1', '关键词2']
          }
        ]
      }

      vi.mocked(aiApi.analyzeTopics).mockResolvedValueOnce(mockResponse)

      const text = '这是测试文本'
      const result = await store.analyzeTopics(text)

      expect(aiApi.analyzeTopics).toHaveBeenCalledWith(text)
      expect(result).toEqual(mockResponse)
      expect(store.topicResult).toEqual(mockResponse)
      expect(store.loading).toBe(false)
    })
  })

  describe('analyzeTrends', () => {
    it('应该正确处理趋势分析请求', async () => {
      const store = useAIStore()
      const mockResponse = {
        keyword: '测试关键词',
        period: '7d',
        trends: [
          {
            date: '2024-03-20',
            frequency: 10,
            sentiment: 0.5
          }
        ],
        relatedTopics: [
          {
            topic: '相关主题1',
            correlation: 0.8
          }
        ]
      }

      vi.mocked(aiApi.analyzeTrends).mockResolvedValueOnce(mockResponse)

      const keyword = '测试关键词'
      const timeRange: [string, string] = ['2024-03-13', '2024-03-20']
      const result = await store.analyzeTrends(keyword, timeRange)

      expect(aiApi.analyzeTrends).toHaveBeenCalledWith(keyword, timeRange)
      expect(result).toEqual(mockResponse)
      expect(store.trendResult).toEqual(mockResponse)
      expect(store.loading).toBe(false)
    })
  })

  describe('clearResults', () => {
    it('应该正确清除所有结果', () => {
      const store = useAIStore()
      
      // 设置一些测试数据
      store.sentimentResult = { sentiment: 'positive', score: 0.8, keywords: [] }
      store.summaryResult = { originalText: '', summary: '', keyPoints: [], wordCount: 0 }
      store.topicResult = { text: '', topics: [] }
      store.trendResult = { keyword: '', period: '', trends: [], relatedTopics: [] }

      store.clearResults()

      expect(store.sentimentResult).toBeNull()
      expect(store.summaryResult).toBeNull()
      expect(store.topicResult).toBeNull()
      expect(store.trendResult).toBeNull()
    })
  })
}) 