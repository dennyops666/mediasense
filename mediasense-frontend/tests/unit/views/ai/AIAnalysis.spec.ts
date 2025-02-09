import { describe, it, expect, vi, beforeEach } from 'vitest'
import AIAnalysis from '@/views/ai/AIAnalysis.vue'
import { createTestingPinia } from '@pinia/testing'
import { useAIStore } from '@/stores/ai'
import { nextTick } from 'vue'
import { createMountComponent } from '../../../setup'

// Mock data
const mockSentimentResult = {
  sentiment: 'positive',
  score: 0.85,
  keywords: ['好', '优秀', '满意']
}

const mockSummaryResult = {
  summary: '这是一段测试文本的摘要。',
  length: 100
}

const mockTopicResult = {
  topics: ['技术', '创新', '发展'],
  confidence: [0.9, 0.8, 0.7]
}

const mockTrendResult = {
  trends: ['上升', '稳定', '下降'],
  data: [
    { date: '2024-03-01', value: 10 },
    { date: '2024-03-02', value: 15 },
    { date: '2024-03-03', value: 12 }
  ]
}

describe('AIAnalysis.vue', () => {
  let wrapper
  let store

  const mountComponent = createMountComponent(AIAnalysis, {
    global: {
      plugins: [
        createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            ai: {
              sentimentResult: null,
              summaryResult: null,
              topicResult: null,
              trendResult: null,
              loading: false,
              error: null
            }
          }
        })
      ]
    }
  })

  beforeEach(() => {
    wrapper = mountComponent()
    store = useAIStore()
    
    // 模拟 store 方法
    store.analyzeSentiment = vi.fn().mockResolvedValue(mockSentimentResult)
    store.analyzeSummary = vi.fn().mockResolvedValue(mockSummaryResult)
    store.analyzeTopics = vi.fn().mockResolvedValue(mockTopicResult)
    store.analyzeTrends = vi.fn().mockResolvedValue(mockTrendResult)
    store.clearResults = vi.fn()
  })

  describe('情感分析', () => {
    it('应该正确处理情感分析表单提交', async () => {
      const text = '这是一段测试文本'
      const input = wrapper.findComponent({ name: 'el-input' })
      await input.vm.$emit('input', text)
      
      const form = wrapper.find('.sentiment-form')
      await form.trigger('submit.prevent')

      expect(store.analyzeSentiment).toHaveBeenCalledWith(text)
      await nextTick()
      expect(store.loading).toBe(false)
    })

    it('应该正确显示情感分析结果', async () => {
      store.sentimentResult = mockSentimentResult
      await nextTick()

      const result = wrapper.find('.sentiment-result')
      expect(result.exists()).toBe(true)
      expect(result.text()).toContain('积极')
      expect(result.text()).toContain('0.85')
      expect(result.text()).toContain('好')
      expect(result.text()).toContain('优秀')
    })
  })

  describe('文本摘要', () => {
    it('应该正确处理文本摘要表单提交', async () => {
      const text = '这是一段需要摘要的长文本'
      const input = wrapper.findComponent({ name: 'el-input' })
      await input.vm.$emit('input', text)
      
      const form = wrapper.find('.summary-form')
      await form.trigger('submit.prevent')

      expect(store.analyzeSummary).toHaveBeenCalledWith(text)
      await nextTick()
      expect(store.loading).toBe(false)
    })

    it('应该正确显示文本摘要结果', async () => {
      store.summaryResult = mockSummaryResult
      await nextTick()

      const result = wrapper.find('.summary-result')
      expect(result.exists()).toBe(true)
      expect(result.text()).toContain(mockSummaryResult.summary)
      expect(result.text()).toContain('100 字')
    })
  })

  describe('主题分析', () => {
    it('应该正确处理主题分析表单提交', async () => {
      const text = '这是一段需要分析主题的文本'
      const input = wrapper.findComponent({ name: 'el-input' })
      await input.vm.$emit('input', text)
      
      const form = wrapper.find('.topic-form')
      await form.trigger('submit.prevent')

      expect(store.analyzeTopics).toHaveBeenCalledWith(text)
      await nextTick()
      expect(store.loading).toBe(false)
    })

    it('应该正确显示主题分析结果', async () => {
      store.topicResult = mockTopicResult
      await nextTick()

      const result = wrapper.find('.topic-result')
      expect(result.exists()).toBe(true)
      expect(result.text()).toContain('技术')
      expect(result.text()).toContain('创新')
      expect(result.text()).toContain('90%')
      expect(result.text()).toContain('80%')
    })
  })

  describe('趋势分析', () => {
    it('应该正确处理趋势分析表单提交', async () => {
      const text = '这是一段需要分析趋势的文本'
      const input = wrapper.findComponent({ name: 'el-input' })
      await input.vm.$emit('input', text)
      
      const form = wrapper.find('.trend-form')
      await form.trigger('submit.prevent')

      expect(store.analyzeTrends).toHaveBeenCalledWith(text)
      await nextTick()
      expect(store.loading).toBe(false)
    })

    it('应该正确显示趋势分析结果', async () => {
      store.trendResult = mockTrendResult
      await nextTick()

      const result = wrapper.find('.trend-result')
      expect(result.exists()).toBe(true)
      expect(result.text()).toContain('上升')
      expect(result.text()).toContain('稳定')
      expect(result.text()).toContain('2024-03-01')
      expect(result.text()).toContain('10')
    })
  })

  describe('标签页切换', () => {
    it('应该在切换标签页时清除结果', async () => {
      store.sentimentResult = mockSentimentResult
      await nextTick()

      const tab = wrapper.findComponent({ name: 'el-tab-pane' })
      await tab.vm.$emit('click')
      await nextTick()

      expect(store.clearResults).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该正确处理分析错误', async () => {
      store.error = '分析失败'
      await nextTick()

      const errorMessage = wrapper.find('.error-message')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toBe('分析失败')
    })
  })
}) 