import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { useAIStore } from '@/stores/ai'
import { useAI } from '@/composables/useAI'
import { setActivePinia } from 'pinia'

describe('useAI', () => {
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      stubActions: false
    })
    setActivePinia(pinia)
    store = useAIStore()

    // 模拟 store 方法
    store.analyzeSentiment = vi.fn()
    store.generateSummary = vi.fn()
    store.analyzeTopics = vi.fn()
    store.analyzeTrends = vi.fn()
  })

  it('初始化时应该有默认值', () => {
    const { loading, error } = useAI()
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够分析情感', async () => {
    const mockResult = { sentiment: 'positive', score: 0.85 }
    store.analyzeSentiment.mockResolvedValue({ data: mockResult })

    const text = '这是一段测试文本'
    const { analyzeSentiment } = useAI()
    const result = await analyzeSentiment(text)

    expect(store.analyzeSentiment).toHaveBeenCalledWith(text)
    expect(result).toEqual(mockResult)
  })

  it('应该能够生成摘要', async () => {
    const mockResult = '这是生成的摘要'
    store.generateSummary.mockResolvedValue({ data: mockResult })

    const text = '这是一段需要摘要的文本'
    const { generateSummary } = useAI()
    const result = await generateSummary(text)

    expect(store.generateSummary).toHaveBeenCalledWith(text)
    expect(result).toEqual(mockResult)
  })

  it('应该能够分析主题', async () => {
    const mockResult = ['主题1', '主题2']
    store.analyzeTopics.mockResolvedValue({ data: mockResult })

    const text = '这是一段需要分析主题的文本'
    const { analyzeTopics } = useAI()
    const result = await analyzeTopics(text)

    expect(store.analyzeTopics).toHaveBeenCalledWith(text)
    expect(result).toEqual(mockResult)
  })

  it('应该能够分析趋势', async () => {
    const mockResult = ['趋势1', '趋势2']
    store.analyzeTrends.mockResolvedValue({ data: mockResult })

    const text = '这是一段需要分析趋势的文本'
    const { analyzeTrends } = useAI()
    const result = await analyzeTrends(text)

    expect(store.analyzeTrends).toHaveBeenCalledWith(text)
    expect(result).toEqual(mockResult)
  })

  it('应该正确处理错误', async () => {
    const mockError = new Error('分析失败')
    store.analyzeSentiment.mockRejectedValue(mockError)

    const text = '这是一段测试文本'
    const { analyzeSentiment, error } = useAI()
    
    try {
      await analyzeSentiment(text)
    } catch (err) {
      expect(err).toBe(mockError)
      expect(error.value).toBe(mockError.message)
    }
  })
})

