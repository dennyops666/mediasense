import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import AIAnalysis from '@/views/ai/AIAnalysis.vue'
import { useAIStore } from '@/stores/ai'
import { ElMessage } from 'element-plus'
import AIBatchProgress from '@/components/ai/AIBatchProgress.vue'
import AIKeywordsCloud from '@/components/ai/AIKeywordsCloud.vue'
import AIResultComparison from '@/components/ai/AIResultComparison.vue'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('AI分析流程集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/ai/analysis',
        name: 'ai-analysis',
        component: AIAnalysis
      },
      {
        path: '/ai/batch',
        name: 'AIBatch',
        component: AIBatchProgress
      },
      {
        path: '/ai/keywords',
        name: 'AIKeywords',
        component: AIKeywordsCloud
      },
      {
        path: '/ai/comparison',
        name: 'AIComparison',
        component: AIResultComparison
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

  describe('批量分析进度', () => {
    it('应该显示批量分析任务列表', async () => {
      const wrapper = mount(AIBatchProgress, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                batchTasks: [
                  {
                    id: '1',
                    name: '批量分析任务1',
                    status: 'running',
                    progress: 60,
                    total: 100,
                    completed: 60,
                    failed: 5,
                    startTime: '2024-03-20T10:00:00Z'
                  }
                ],
                keywordsData: [
                  { name: '关键词1', value: 100 },
                  { name: '关键词2', value: 80 }
                ],
                comparisonResults: {
                  sentiment: {
                    before: { positive: 0.6, negative: 0.4 },
                    after: { positive: 0.7, negative: 0.3 }
                  },
                  keywords: [
                    { word: '关键词1', scoreBefore: 0.8, scoreAfter: 0.9 },
                    { word: '关键词2', scoreBefore: 0.6, scoreAfter: 0.7 }
                  ]
                },
                loading: false,
                error: null
              }
            }
          })]
        }
      })

      const tasks = wrapper.findAll('[data-test="batch-task"]')
      expect(tasks).toHaveLength(1)
      expect(tasks[0].text()).toContain('批量分析任务1')
      expect(tasks[0].text()).toContain('60%')
    })

    it('应该能暂停和恢复任务', async () => {
      const wrapper = mount(AIBatchProgress, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                batchTasks: [{
                  id: '1',
                  status: 'paused'
                }]
              }
            }
          })]
        }
      })

      const pauseButton = wrapper.find('[data-test="pause-task-1"]')
      await pauseButton.trigger('click')
      expect(store.pauseBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已暂停')

      store.$patch({
        batchTasks: [{
          id: '1',
          status: 'paused'
        }]
      })

      const resumeButton = wrapper.find('[data-test="resume-task-1"]')
      await resumeButton.trigger('click')
      expect(store.resumeBatchTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已恢复')
    })
  })

  describe('关键词云分析', () => {
    it('应该显示关键词云', async () => {
      const wrapper = mount(AIKeywordsCloud, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                keywordsData: [
                  { name: '关键词1', value: 100 },
                  { name: '关键词2', value: 80 }
                ]
              }
            }
          })]
        }
      })

      const chart = wrapper.find('[data-test="keywords-cloud"]')
      expect(chart.exists()).toBe(true)
    })

    it('应该能切换时间范围', async () => {
      const wrapper = mount(AIKeywordsCloud, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                keywordsData: [
                  { name: '关键词1', value: 100 },
                  { name: '关键词2', value: 80 }
                ]
              }
            }
          })]
        }
      })

      const timeSelect = wrapper.find('[data-test="time-range"]')
      await timeSelect.setValue('7d')
      await timeSelect.trigger('change')

      expect(store.fetchKeywords).toHaveBeenCalledWith('7d')
    })

    it('应该能刷新数据', async () => {
      const wrapper = mount(AIKeywordsCloud, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                keywordsData: [
                  { name: '关键词1', value: 100 },
                  { name: '关键词2', value: 80 }
                ]
              }
            }
          })]
        }
      })

      const refreshButton = wrapper.find('[data-test="refresh-button"]')
      await refreshButton.trigger('click')

      expect(store.fetchKeywords).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('数据已刷新')
    })
  })

  describe('结果比较分析', () => {
    it('应该显示情感分析比较', async () => {
      const wrapper = mount(AIResultComparison, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                comparisonResults: {
                  sentiment: {
                    before: { positive: 0.6, negative: 0.4 },
                    after: { positive: 0.7, negative: 0.3 }
                  }
                }
              }
            }
          })]
        }
      })

      const sentiment = wrapper.find('[data-test="sentiment-comparison"]')
      expect(sentiment.exists()).toBe(true)
      expect(sentiment.text()).toContain('70%')
      expect(sentiment.text()).toContain('30%')
    })

    it('应该显示关键词得分比较', async () => {
      const wrapper = mount(AIResultComparison, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                comparisonResults: {
                  keywords: [
                    { word: '关键词1', scoreBefore: 0.8, scoreAfter: 0.9 },
                    { word: '关键词2', scoreBefore: 0.6, scoreAfter: 0.7 }
                  ]
                }
              }
            }
          })]
        }
      })

      const keywords = wrapper.findAll('[data-test="keyword-item"]')
      expect(keywords).toHaveLength(2)
      expect(keywords[0].text()).toContain('关键词1')
      expect(keywords[0].text()).toContain('0.9')
    })

    it('应该能导出比较结果', async () => {
      const wrapper = mount(AIResultComparison, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                comparisonResults: {
                  keywords: [
                    { word: '关键词1', scoreBefore: 0.8, scoreAfter: 0.9 },
                    { word: '关键词2', scoreBefore: 0.6, scoreAfter: 0.7 }
                  ]
                }
              }
            }
          })]
        }
      })

      const exportButton = wrapper.find('[data-test="export-button"]')
      await exportButton.trigger('click')

      expect(store.exportComparison).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('比较结果已导出')
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      store.$patch({ error: '加载失败' })

      const wrapper = mount(AIBatchProgress, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                error: '加载失败'
              }
            }
          })]
        }
      })

      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该能重试加载', async () => {
      store.$patch({ error: '加载失败' })

      const wrapper = mount(AIBatchProgress, {
        global: {
          plugins: [router, createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              ai: {
                error: '加载失败'
              }
            }
          })]
        }
      })

      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')

      expect(store.fetchBatchTasks).toHaveBeenCalled()
    })
  })
}) 