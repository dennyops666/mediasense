import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as aiApi from '@/api/ai'
import request from '@/utils/request'

// Mock request module
vi.mock('@/utils/request', () => ({
  default: {
    post: vi.fn()
  }
}))

describe('AI API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('analyzeSentiment', () => {
    it('应该正确调用情感分析接口', async () => {
      const mockResponse = {
        sentiment: 'positive',
        score: 0.85,
        keywords: ['优秀', '出色', '满意']
      }
      
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      const text = '这是一段测试文本'
      const result = await aiApi.analyzeSentiment(text)
      
      expect(request.post).toHaveBeenCalledWith('/ai/sentiment', { text })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('generateSummary', () => {
    it('应该正确调用文本摘要接口', async () => {
      const mockResponse = {
        originalText: '这是原始文本',
        summary: '这是摘要',
        keyPoints: ['要点1', '要点2'],
        wordCount: 100
      }
      
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      const text = '这是一段测试文本'
      const maxLength = 200
      const result = await aiApi.generateSummary(text, maxLength)
      
      expect(request.post).toHaveBeenCalledWith('/ai/summary', { text, maxLength })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('analyzeTopics', () => {
    it('应该正确调用主题分析接口', async () => {
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
      
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      const text = '这是一段测试文本'
      const result = await aiApi.analyzeTopics(text)
      
      expect(request.post).toHaveBeenCalledWith('/ai/topics', { text })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('analyzeTrends', () => {
    it('应该正确调用趋势分析接口', async () => {
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
      
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      const keyword = '测试关键词'
      const timeRange: [string, string] = ['2024-03-13', '2024-03-20']
      const result = await aiApi.analyzeTrends(keyword, timeRange)
      
      expect(request.post).toHaveBeenCalledWith('/ai/trends', { keyword, timeRange })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('batchAnalyze', () => {
    it('应该正确调用批量分析接口', async () => {
      const mockResponse = [
        {
          sentiment: 'positive',
          score: 0.85,
          keywords: ['优秀', '出色']
        },
        {
          sentiment: 'negative',
          score: 0.3,
          keywords: ['失望', '糟糕']
        }
      ]
      
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      const texts = ['文本1', '文本2']
      const result = await aiApi.batchAnalyze(texts)
      
      expect(request.post).toHaveBeenCalledWith('/ai/batch-analyze', { texts })
      expect(result).toEqual(mockResponse)
    })
  })
}) 