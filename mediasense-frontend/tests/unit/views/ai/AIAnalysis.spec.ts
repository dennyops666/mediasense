import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import AIAnalysis from '@/views/ai/AIAnalysis.vue'
import { useAIStore } from '@/stores/ai'
import type { SentimentAnalysis } from '@/types/api'
import { nextTick } from 'vue'

// Mock ECharts
vi.mock('vue-echarts', () => ({
  default: {
    name: 'v-chart',
    template: '<div class="echarts-mock"></div>'
  }
}))

const mockAnalysisResult = {
  sentiment: {
    sentiment: 'positive',
    score: 0.85,
    keywords: ['优秀', '出色', '满意']
  } as SentimentAnalysis,
  summary: {
    originalText: '这是原始文本',
    summary: '这是一段测试摘要',
    keyPoints: ['要点1', '要点2'],
    wordCount: 100
  },
  topics: {
    text: '这是测试文本',
    topics: [
      {
        name: '话题1',
        confidence: 0.9,
        keywords: ['关键词1', '关键词2']
      }
    ]
  },
  trends: {
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
}

describe('AIAnalysis.vue', () => {
  let wrapper
  let store
  let pinia

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useAIStore()
    
    // Mock store methods
    store.analyzeSentiment = vi.fn().mockResolvedValue(mockAnalysisResult.sentiment)
    store.generateSummary = vi.fn().mockResolvedValue(mockAnalysisResult.summary)
    store.analyzeTopics = vi.fn().mockResolvedValue(mockAnalysisResult.topics)
    store.analyzeTrends = vi.fn().mockResolvedValue(mockAnalysisResult.trends)

    wrapper = mount(AIAnalysis, {
      global: {
        plugins: [ElementPlus, pinia],
        stubs: {
          'v-chart': true,
          'el-tabs': {
            template: '<div><slot></slot></div>',
            emits: ['tab-change']
          },
          'el-tab-pane': {
            template: '<div><slot></slot></div>'
          },
          'el-card': {
            template: '<div><slot></slot><slot name="header"></slot></div>'
          },
          'el-form': {
            template: '<form @submit.prevent="$emit(\'submit\')"><slot></slot></form>'
          },
          'el-form-item': {
            template: '<div><slot></slot></div>'
          },
          'el-input': {
            template: '<input type="text" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot></slot></button>',
            emits: ['click']
          },
          'el-tag': {
            template: '<span><slot></slot></span>'
          }
        }
      },
      data() {
        return {
          activeTab: 'sentiment',
          inputText: '',
          sentimentResult: null,
          summaryResult: null,
          topicResult: null,
          trendResult: null
        }
      }
    })

    await nextTick()
  })

  describe('情感分析', () => {
    it('应该正确处理情感分析表单提交', async () => {
      const input = wrapper.find('input')
      await input.setValue('这是一段测试文本')
      
      const button = wrapper.find('button')
      await button.trigger('click')
      
      expect(store.analyzeSentiment).toHaveBeenCalledWith('这是一段测试文本')
    })

    it('应该正确显示情感分析结果', async () => {
      wrapper.vm.sentimentResult = mockAnalysisResult.sentiment
      await nextTick()
      
      const resultElement = wrapper.find('.analysis-result')
      expect(resultElement.exists()).toBe(true)
      expect(resultElement.text()).toContain('积极')
      expect(resultElement.text()).toContain('85%')
    })
  })

  describe('文本摘要', () => {
    it('应该正确处理文本摘要表单提交', async () => {
      wrapper.vm.activeTab = 'summary'
      await nextTick()
      
      const input = wrapper.find('input')
      await input.setValue('这是一段需要摘要的文本')
      
      const button = wrapper.find('button')
      await button.trigger('click')
      
      expect(store.generateSummary).toHaveBeenCalledWith('这是一段需要摘要的文本')
    })
  })

  describe('主题分析', () => {
    it('应该正确处理主题分析表单提交', async () => {
      wrapper.vm.activeTab = 'topic'
      await nextTick()
      
      const input = wrapper.find('input')
      await input.setValue('这是一段需要分析主题的文本')
      
      const button = wrapper.find('button')
      await button.trigger('click')
      
      expect(store.analyzeTopics).toHaveBeenCalledWith('这是一段需要分析主题的文本')
    })
  })

  describe('趋势分析', () => {
    it('应该正确处理趋势分析表单提交', async () => {
      wrapper.vm.activeTab = 'trend'
      await nextTick()
      
      const input = wrapper.find('input')
      await input.setValue('这是一段需要分析趋势的文本')
      
      const button = wrapper.find('button')
      await button.trigger('click')
      
      expect(store.analyzeTrends).toHaveBeenCalledWith('这是一段需要分析趋势的文本', undefined)
    })
  })

  describe('标签页切换', () => {
    it('应该在切换标签页时清除结果', async () => {
      wrapper.vm.sentimentResult = mockAnalysisResult.sentiment
      await nextTick()
      
      wrapper.vm.handleTabChange('summary')
      await nextTick()
      
      expect(wrapper.vm.sentimentResult).toBeNull()
    })
  })
}) 