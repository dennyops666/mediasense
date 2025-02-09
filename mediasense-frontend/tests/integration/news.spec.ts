import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import NewsList from '@/views/news/NewsList.vue'
import NewsDetail from '@/views/news/NewsDetail.vue'
import { useNewsStore } from '@/stores/news'
import { ElMessage, ElMessageBox } from 'element-plus'
import CrawlerConfigForm from '@/components/crawler/CrawlerConfigForm.vue'
import CrawlerTaskList from '@/components/crawler/CrawlerTaskList.vue'
import CrawlerDataList from '@/components/crawler/CrawlerDataList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import * as crawlerApi from '@/api/crawler'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue(true)
  }
}))

const mockNews = [
  {
    id: '1',
    title: '测试新闻1',
    content: '内容1',
    category: '科技',
    source: '来源1',
    publishTime: '2024-03-20T10:00:00Z',
    url: 'http://example.com/news/1',
    isFavorite: false
  },
  {
    id: '2',
    title: '测试新闻2',
    content: '内容2',
    category: '财经',
    source: '来源2',
    publishTime: '2024-03-20T11:00:00Z',
    url: 'http://example.com/news/2',
    isFavorite: true
  }
]

describe('新闻管理集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/news',
        name: 'news-list',
        component: NewsList
      },
      {
        path: '/news/:id',
        name: 'news-detail',
        component: NewsDetail,
        props: true
      }
    ]
  })

  beforeEach(async () => {
    vi.clearAllMocks()
    router.push('/news')
    await router.isReady()
  })

  describe('新闻列表页面', () => {
    it('应该正确显示新闻列表', async () => {
      const wrapper = mount(NewsList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  newsList: mockNews,
                  loading: false,
                  categories: ['科技', '财经']
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: `
                <div class="el-table">
                  <div v-for="item in data" :key="item.id" class="news-item">
                    <slot :row="item"></slot>
                  </div>
                </div>
              `,
              props: ['data']
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot :row="$parent.row"></slot></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot/></span>'
            },
            'el-select': {
              template: '<select class="el-select" @change="$emit(\'update:modelValue\', $event.target.value)"><slot/></select>'
            },
            'el-option': {
              template: '<option :value="value"><slot/></option>',
              props: ['value']
            },
            'el-input': {
              template: '<input class="el-input" @input="$emit(\'update:modelValue\', $event.target.value)" />',
              props: ['modelValue']
            }
          }
        }
      })

      const newsItems = wrapper.findAll('.news-item')
      expect(newsItems).toHaveLength(2)
      expect(newsItems[0].text()).toContain('测试新闻1')
      expect(newsItems[1].text()).toContain('测试新闻2')
    })

    it('应该能按分类筛选新闻', async () => {
      const wrapper = mount(NewsList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  newsList: mockNews,
                  loading: false,
                  categories: ['科技', '财经']
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: '<div class="el-table"><slot/></div>'
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot/></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot/></span>'
            },
            'el-select': {
              template: '<select class="el-select" @change="$emit(\'update:modelValue\', $event.target.value)"><slot/></select>'
            },
            'el-option': {
              template: '<option :value="value"><slot/></option>',
              props: ['value']
            }
          }
        }
      })

      const categorySelect = wrapper.find('.el-select')
      await categorySelect.setValue('科技')
      await categorySelect.trigger('change')

      const store = useNewsStore()
      expect(store.filterNewsByCategory).toHaveBeenCalledWith('科技')
    })

    it('应该能搜索新闻', async () => {
      const wrapper = mount(NewsList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  newsList: mockNews,
                  loading: false,
                  categories: ['科技', '财经']
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: '<div class="el-table"><slot/></div>'
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot/></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot/></span>'
            },
            'el-input': {
              template: '<input class="el-input" @input="$emit(\'update:modelValue\', $event.target.value)" />',
              props: ['modelValue']
            }
          }
        }
      })

      const searchInput = wrapper.find('.el-input')
      await searchInput.setValue('测试新闻1')
      await searchInput.trigger('input')

      const store = useNewsStore()
      expect(store.searchNews).toHaveBeenCalledWith('测试新闻1')
    })
  })

  describe('新闻详情页面', () => {
    it('应该正确显示新闻详情', async () => {
      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: mockNews[0],
                  loading: false
                }
              }
            })
          ],
          stubs: {
            'el-card': {
              template: '<div class="el-card"><slot/></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot/></span>'
            }
          }
        },
        props: {
          id: '1'
        }
      })

      expect(wrapper.find('.news-title').text()).toBe('测试新闻1')
      expect(wrapper.find('.news-content').text()).toBe('内容1')
      expect(wrapper.find('.news-source').text()).toContain('来源1')
      expect(wrapper.find('.news-category').text()).toContain('科技')
    })

    it('应该在加载失败时显示错误信息', async () => {
      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: null,
                  loading: false,
                  error: '加载失败'
                }
              }
            })
          ],
          stubs: {
            'el-alert': {
              template: '<div class="el-alert error-message"><slot/></div>'
            }
          }
        },
        props: {
          id: '1'
        }
      })

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('加载失败')
    })
  })

  describe('新闻操作', () => {
    it('应该能分享新闻', async () => {
      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: mockNews[0],
                  loading: false
                }
              }
            })
          ],
          stubs: {
            'el-card': {
              template: '<div class="el-card"><slot/></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            }
          }
        },
        props: {
          id: '1'
        }
      })

      const shareButton = wrapper.find('.share-button')
      await shareButton.trigger('click')

      expect(ElMessage.success).toHaveBeenCalledWith('分享链接已复制到剪贴板')
    })

    it('应该能收藏新闻', async () => {
      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: mockNews[0],
                  loading: false
                }
              }
            })
          ],
          stubs: {
            'el-card': {
              template: '<div class="el-card"><slot/></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot/></button>'
            }
          }
        },
        props: {
          id: '1'
        }
      })

      const favoriteButton = wrapper.find('.favorite-button')
      await favoriteButton.trigger('click')

      const store = useNewsStore()
      expect(store.toggleFavorite).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('收藏成功')
    })
  })
})

describe('新闻爬虫集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/crawler',
        children: [
          {
            path: 'config',
            component: CrawlerConfigForm
          },
          {
            path: 'list',
            component: CrawlerTaskList
          },
          {
            path: 'data',
            component: CrawlerDataList
          }
        ]
      }
    ]
  })

  const mockConfig = {
    name: '测试新闻爬虫',
    type: 'news',
    url: 'http://example.com/news',
    enabled: true,
    targetUrl: 'http://example.com/news',
    method: 'GET',
    headers: [],
    selectors: [
      { field: 'title', selector: '.news-title', type: 'css' },
      { field: 'content', selector: '.news-content', type: 'css' },
      { field: 'date', selector: '.news-date', type: 'css' }
    ],
    timeout: 30,
    retries: 3,
    concurrency: 1,
    selector: {
      title: '.news-title',
      content: '.news-content'
    },
    userAgent: 'Mozilla/5.0'
  }

  const mockTask = {
    id: '1',
    name: '测试新闻爬虫任务',
    type: 'news',
    schedule: '0 0 * * *',
    config: mockConfig,
    status: 'running',
    lastRunTime: '2024-03-20T10:00:00Z',
    count: 100,
    configId: '1',
    startTime: '2024-03-20T10:00:00Z',
    totalItems: 100,
    successItems: 80,
    failedItems: 20,
    createdAt: '2024-03-20T10:00:00Z',
    updatedAt: '2024-03-20T10:00:00Z'
  }

  const mockData = [
    {
      id: '1',
      taskId: '1',
      title: '测试新闻1',
      content: '测试内容1',
      url: 'http://example.com/news/1',
      source: '测试来源',
      category: '测试分类',
      publishTime: '2024-03-20T10:00:00Z',
      crawlTime: '2024-03-20T10:00:00Z',
      rawData: {}
    },
    {
      id: '2',
      taskId: '1',
      title: '测试新闻2',
      content: '测试内容2',
      url: 'http://example.com/news/2',
      source: '测试来源',
      category: '测试分类',
      publishTime: '2024-03-20T11:00:00Z',
      crawlTime: '2024-03-20T11:00:00Z',
      rawData: {}
    }
  ]

  beforeEach(async () => {
    vi.clearAllMocks()
    await router.push('/crawler/config')
  })

  describe('爬虫配置流程', () => {
    it('应该能成功创建新闻爬虫配置', async () => {
      const wrapper = mount(CrawlerConfigForm, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  configs: [],
                  loading: false
                }
              }
            })
          ]
        },
        props: {
          mode: 'create'
        }
      })

      vi.mocked(crawlerApi.createCrawlerConfig).mockResolvedValue(mockConfig)

      await wrapper.setData({
        formData: mockConfig
      })

      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(crawlerApi.createCrawlerConfig).toHaveBeenCalledWith(mockConfig)
      expect(ElMessage.success).toHaveBeenCalledWith('创建爬虫配置成功')
    })

    it('应该能验证配置的有效性', async () => {
      const wrapper = mount(CrawlerConfigForm, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn
            })
          ]
        },
        props: {
          mode: 'create'
        }
      })

      vi.mocked(crawlerApi.testConfig).mockResolvedValue({ success: true })

      await wrapper.setData({
        formData: mockConfig
      })

      const testButton = wrapper.find('[data-test="test-button"]')
      await testButton.trigger('click')

      expect(crawlerApi.testConfig).toHaveBeenCalledWith(mockConfig)
      expect(ElMessage.success).toHaveBeenCalledWith('测试成功')
    })
  })

  describe('任务管理流程', () => {
    it('应该能启动爬虫任务', async () => {
      const wrapper = mount(CrawlerTaskList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  tasks: [mockTask],
                  loading: false
                }
              }
            })
          ]
        }
      })

      vi.mocked(crawlerApi.startTask).mockResolvedValue({ success: true })

      const startButton = wrapper.find('[data-test="start-task-1"]')
      await startButton.trigger('click')

      expect(crawlerApi.startTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('启动任务成功')
    })

    it('应该能监控任务进度', async () => {
      const wrapper = mount(CrawlerTaskList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  tasks: [mockTask],
                  loading: false
                }
              }
            })
          ]
        }
      })

      const progressBar = wrapper.find('[data-test="task-progress"]')
      expect(progressBar.attributes('percentage')).toBe('80')
    })
  })

  describe('数据管理流程', () => {
    it('应该能查看采集到的数据', async () => {
      // Mock crawlerApi
      vi.mock('@/api/crawler', () => ({
        getTaskData: vi.fn().mockResolvedValue({
          items: mockData,
          total: 2
        })
      }))

      const wrapper = mount(CrawlerDataList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  currentTaskData: mockData,
                  loading: false
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: '<div class="el-table"><slot></slot></div>'
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot></slot></div>'
            },
            'el-button': {
              template: '<button class="el-button" @click="$emit(\'click\')"><slot></slot></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot></slot></span>'
            }
          }
        },
        props: {
          taskId: '1'
        }
      })

      await wrapper.vm.$nextTick()

      const store = useCrawlerStore()
      expect(store.fetchTaskData).toHaveBeenCalledWith('1')
      expect(wrapper.findAll('.el-table-column')).toHaveLength(2)
    })

    it('应该能导出采集数据', async () => {
      // Mock crawlerApi
      vi.mock('@/api/crawler', () => ({
        exportTaskData: vi.fn().mockResolvedValue({
          success: true,
          url: 'http://example.com/export/1'
        })
      }))

      const wrapper = mount(CrawlerDataList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  currentTaskData: mockData,
                  loading: false
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: '<div class="el-table"><slot></slot></div>'
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot></slot></div>'
            },
            'el-button': {
              template: '<button class="el-button export-button" @click="$emit(\'click\')"><slot></slot></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot></slot></span>'
            }
          }
        },
        props: {
          taskId: '1'
        }
      })

      await wrapper.vm.$nextTick()

      const exportButton = wrapper.find('.export-button')
      await exportButton.trigger('click')

      const store = useCrawlerStore()
      expect(store.exportTaskData).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('数据导出成功')
    })
  })

  describe('错误处理流程', () => {
    it('应该处理配置创建失败', async () => {
      // Mock crawlerApi
      vi.mock('@/api/crawler', () => ({
        createCrawlerConfig: vi.fn().mockRejectedValue(new Error('创建失败'))
      }))

      const wrapper = mount(CrawlerConfigForm, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  configs: [],
                  loading: false,
                  error: null
                }
              }
            })
          ],
          stubs: {
            'el-form': {
              template: '<form class="el-form" @submit.prevent><slot></slot></form>'
            },
            'el-form-item': {
              template: '<div class="el-form-item"><slot></slot></div>'
            },
            'el-input': {
              template: '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
              props: ['modelValue'],
              emits: ['update:modelValue']
            },
            'el-button': {
              template: '<button class="el-button submit-button" @click="$emit(\'click\')"><slot></slot></button>'
            },
            'el-alert': {
              template: '<div class="el-alert error-message"><slot></slot></div>'
            }
          }
        },
        props: {
          mode: 'create'
        }
      })

      await wrapper.setData({
        formData: mockConfig
      })

      const submitButton = wrapper.find('.submit-button')
      await submitButton.trigger('click')

      const store = useCrawlerStore()
      expect(store.createConfig).toHaveBeenCalledWith(mockConfig)
      expect(ElMessage.error).toHaveBeenCalledWith('创建爬虫配置失败')
      expect(wrapper.find('.error-message').exists()).toBe(true)
    })

    it('应该处理任务启动失败', async () => {
      // Mock crawlerApi
      vi.mock('@/api/crawler', () => ({
        startTask: vi.fn().mockRejectedValue(new Error('启动失败'))
      }))

      const wrapper = mount(CrawlerTaskList, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  tasks: [mockTask],
                  loading: false,
                  error: null
                }
              }
            })
          ],
          stubs: {
            'el-table': {
              template: '<div class="el-table"><slot></slot></div>'
            },
            'el-table-column': {
              template: '<div class="el-table-column"><slot></slot></div>'
            },
            'el-button': {
              template: '<button class="el-button start-button" @click="$emit(\'click\')"><slot></slot></button>'
            },
            'el-tag': {
              template: '<span class="el-tag"><slot></slot></span>'
            },
            'el-alert': {
              template: '<div class="el-alert error-message"><slot></slot></div>'
            }
          }
        }
      })

      await wrapper.vm.$nextTick()

      const startButton = wrapper.find('.start-button')
      await startButton.trigger('click')

      const store = useCrawlerStore()
      expect(store.startTask).toHaveBeenCalledWith('1')
      expect(ElMessage.error).toHaveBeenCalledWith('启动任务失败')
      expect(wrapper.find('.error-message').exists()).toBe(true)
    })
  })
}) 