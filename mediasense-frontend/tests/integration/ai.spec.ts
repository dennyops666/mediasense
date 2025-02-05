import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import AIAnalysis from '@/views/ai/AIAnalysis.vue'
import { useAIStore } from '@/stores/ai'
import { ElMessage } from 'element-plus'

vi.mock('element-plus')

describe('AI分析流程集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/ai/analysis',
        name: 'ai-analysis',
        component: AIAnalysis
      }
    ]
  })

  beforeEach(() => {
    vi.clearAllMocks()
    router.push('/ai/analysis')
  })

  describe('新闻分析流程', () => {
    it('应该完成单篇新闻分析', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAIStore()
      const mockAnalysis = {
        summary: '这是一篇关于科技创新的新闻',
        keywords: ['科技', '创新', 'AI'],
        sentiment: 'positive',
        entities: ['公司A', '技术B'],
        categories: ['科技', '商业']
      }

      // 模拟分析结果
      vi.mocked(store.analyzeNews).mockResolvedValueOnce(mockAnalysis)

      // 输入新闻URL
      await wrapper.find('input[name="newsUrl"]').setValue('https://example.com/news/1')
      
      // 提交分析
      await wrapper.find('.analyze-btn').trigger('click')

      expect(store.analyzeNews).toHaveBeenCalledWith('https://example.com/news/1')

      await wrapper.vm.$nextTick()

      // 验证分析结果显示
      expect(wrapper.find('.summary').text()).toContain('这是一篇关于科技创新的新闻')
      expect(wrapper.find('.sentiment').text()).toContain('positive')
      expect(wrapper.findAll('.keyword')).toHaveLength(3)
      expect(wrapper.findAll('.entity')).toHaveLength(2)
    })

    it('应该完成批量新闻分析', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAIStore()
      const mockBatchResults = [
        {
          url: 'https://example.com/news/1',
          analysis: {
            summary: '新闻1摘要',
            sentiment: 'positive'
          }
        },
        {
          url: 'https://example.com/news/2',
          analysis: {
            summary: '新闻2摘要',
            sentiment: 'neutral'
          }
        }
      ]

      // 模拟批量分析结果
      vi.mocked(store.analyzeBatchNews).mockResolvedValueOnce(mockBatchResults)

      // 上传新闻URL文件
      const file = new File(['url1\nurl2'], 'urls.txt', { type: 'text/plain' })
      const input = wrapper.find('input[type="file"]')
      await input.trigger('change', { target: { files: [file] } })

      // 提交批量分析
      await wrapper.find('.batch-analyze-btn').trigger('click')

      expect(store.analyzeBatchNews).toHaveBeenCalledWith(['url1', 'url2'])

      await wrapper.vm.$nextTick()

      // 验证批量分析结果显示
      const resultItems = wrapper.findAll('.batch-result-item')
      expect(resultItems).toHaveLength(2)
      expect(resultItems[0].text()).toContain('新闻1摘要')
      expect(resultItems[1].text()).toContain('新闻2摘要')
    })
  })

  describe('分析历史记录', () => {
    it('应该正确显示分析历史', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                ai: {
                  analysisHistory: [
                    {
                      id: '1',
                      url: 'https://example.com/news/1',
                      analysis: {
                        summary: '历史分析1',
                        timestamp: '2024-03-20T10:00:00Z'
                      }
                    }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const historyItems = wrapper.findAll('.history-item')
      expect(historyItems).toHaveLength(1)
      expect(historyItems[0].text()).toContain('历史分析1')
    })

    it('应该正确清除分析历史', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                ai: {
                  analysisHistory: [
                    {
                      id: '1',
                      analysis: { summary: '历史分析1' }
                    }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const store = useAIStore()
      vi.mocked(store.clearAnalysisHistory).mockResolvedValueOnce()

      await wrapper.find('.clear-history-btn').trigger('click')

      expect(store.clearAnalysisHistory).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('分析历史已清除')
    })
  })

  describe('分析设置', () => {
    it('应该正确更新分析设置', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAIStore()

      // 更新语言设置
      await wrapper.find('.language-select').trigger('click')
      await wrapper.find('.language-option-zh').trigger('click')

      expect(store.updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        language: 'zh'
      }))

      // 更新分析深度
      await wrapper.find('.depth-select').trigger('click')
      await wrapper.find('.depth-option-deep').trigger('click')

      expect(store.updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        analysisDepth: 'deep'
      }))
    })
  })

  describe('错误处理', () => {
    it('应该正确处理分析失败', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAIStore()
      vi.mocked(store.analyzeNews).mockRejectedValueOnce(new Error('分析失败'))

      await wrapper.find('input[name="newsUrl"]').setValue('https://example.com/news/1')
      await wrapper.find('.analyze-btn').trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('分析失败')
    })

    it('应该正确处理无效URL', async () => {
      const wrapper = mount(AIAnalysis, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      await wrapper.find('input[name="newsUrl"]').setValue('invalid-url')
      await wrapper.find('.analyze-btn').trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('请输入有效的URL')
    })
  })
}) 