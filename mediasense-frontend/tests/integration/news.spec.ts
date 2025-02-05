import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import NewsList from '@/views/news/NewsList.vue'
import NewsDetail from '@/views/news/NewsDetail.vue'
import { useNewsStore } from '@/stores/news'
import { ElMessage } from 'element-plus'

vi.mock('element-plus')

describe('新闻管理流程集成测试', () => {
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

  beforeEach(() => {
    vi.clearAllMocks()
    router.push('/news')
  })

  describe('新闻列表流程', () => {
    it('应该完成新闻列表加载和过滤', async () => {
      const wrapper = mount(NewsList, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useNewsStore()
      const mockNews = [
        {
          id: '1',
          title: '测试新闻1',
          content: '内容1',
          category: '科技',
          source: '来源1',
          publishTime: '2024-03-20T10:00:00Z'
        }
      ]

      // 模拟获取新闻列表
      vi.mocked(store.fetchNewsList).mockResolvedValueOnce({
        list: mockNews,
        total: 100
      })

      // 模拟获取分类和来源
      vi.mocked(store.fetchCategories).mockResolvedValueOnce(['科技', '财经'])
      vi.mocked(store.fetchSources).mockResolvedValueOnce(['来源1', '来源2'])

      await wrapper.vm.$nextTick()

      // 验证初始加载
      expect(store.fetchNewsList).toHaveBeenCalled()
      expect(store.fetchCategories).toHaveBeenCalled()
      expect(store.fetchSources).toHaveBeenCalled()

      // 应用过滤条件
      await wrapper.find('.category-select').trigger('click')
      await wrapper.find('.category-option').trigger('click')

      expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
        category: '科技'
      }))

      // 验证分页
      const pagination = wrapper.findComponent({ name: 'el-pagination' })
      await pagination.vm.$emit('current-change', 2)

      expect(store.fetchNewsList).toHaveBeenCalledWith(expect.objectContaining({
        page: 2
      }))
    })

    it('应该正确处理新闻详情跳转', async () => {
      const wrapper = mount(NewsList, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  newsList: [
                    {
                      id: '1',
                      title: '测试新闻1'
                    }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      await wrapper.find('.news-title-link').trigger('click')
      expect(router.currentRoute.value.path).toBe('/news/1')
    })
  })

  describe('新闻详情流程', () => {
    it('应该完成新闻详情查看和编辑', async () => {
      await router.push('/news/1')

      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useNewsStore()
      const mockNews = {
        id: '1',
        title: '测试新闻1',
        content: '内容1',
        category: '科技',
        source: '来源1',
        publishTime: '2024-03-20T10:00:00Z'
      }

      // 模拟获取新闻详情
      vi.mocked(store.fetchNewsDetail).mockResolvedValueOnce(mockNews)
      await wrapper.vm.$nextTick()

      expect(store.fetchNewsDetail).toHaveBeenCalledWith('1')

      // 进入编辑模式
      await wrapper.find('.edit-news-btn').trigger('click')
      
      // 修改内容
      await wrapper.find('input[name="title"]').setValue('更新后的标题')
      await wrapper.find('textarea[name="content"]').setValue('更新后的内容')

      // 保存更改
      await wrapper.find('.save-news-btn').trigger('click')

      expect(store.updateNews).toHaveBeenCalledWith('1', {
        title: '更新后的标题',
        content: '更新后的内容'
      })
    })

    it('应该正确处理新闻删除', async () => {
      await router.push('/news/1')

      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: {
                    id: '1',
                    title: '测试新闻1'
                  }
                }
              }
            }),
            router
          ]
        }
      })

      const store = useNewsStore()
      vi.mocked(store.deleteNews).mockResolvedValueOnce()

      // 点击删除按钮
      await wrapper.find('.delete-news-btn').trigger('click')
      
      // 确认删除
      await wrapper.find('.confirm-delete-btn').trigger('click')

      expect(store.deleteNews).toHaveBeenCalledWith('1')
      expect(router.currentRoute.value.path).toBe('/news')
    })
  })

  describe('新闻分享功能', () => {
    it('应该正确处理新闻分享', async () => {
      await router.push('/news/1')

      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: {
                    id: '1',
                    title: '测试新闻1'
                  }
                }
              }
            }),
            router
          ]
        }
      })

      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
      global.navigator.clipboard = mockClipboard

      await wrapper.find('.share-news-btn').trigger('click')

      expect(mockClipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('/news/1'))
      expect(ElMessage.success).toHaveBeenCalledWith('分享链接已复制到剪贴板')
    })
  })

  describe('错误处理', () => {
    it('应该正确处理新闻不存在的情况', async () => {
      await router.push('/news/999')

      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useNewsStore()
      vi.mocked(store.fetchNewsDetail).mockRejectedValueOnce(new Error('新闻不存在'))

      await wrapper.vm.$nextTick()

      expect(ElMessage.error).toHaveBeenCalledWith('新闻不存在')
      expect(router.currentRoute.value.path).toBe('/news')
    })

    it('应该正确处理更新失败的情况', async () => {
      await router.push('/news/1')

      const wrapper = mount(NewsDetail, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                news: {
                  currentNews: {
                    id: '1',
                    title: '测试新闻1'
                  }
                }
              }
            }),
            router
          ]
        }
      })

      const store = useNewsStore()
      vi.mocked(store.updateNews).mockRejectedValueOnce(new Error('更新失败'))

      // 进入编辑模式
      await wrapper.find('.edit-news-btn').trigger('click')
      
      // 修改内容
      await wrapper.find('input[name="title"]').setValue('更新后的标题')

      // 保存更改
      await wrapper.find('.save-news-btn').trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('更新失败')
    })
  })
}) 