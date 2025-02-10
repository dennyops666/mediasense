import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createRouter, createWebHistory } from 'vue-router'
import { ref } from 'vue'
import NewsDetail from '@/views/news/NewsDetail.vue'
import { useNewsStore } from '@/stores/news'
import type { News } from '@/types/news'

const mockNews: News = {
  id: '1',
  title: '测试新闻标题',
  content: '测试新闻内容',
  author: '测试作者',
  publishTime: '2024-01-01 12:00:00',
  source: '测试来源',
  category: '测试分类',
  tags: ['标签1', '标签2'],
  views: 100
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/news',
      name: 'NewsList',
      component: () => import('@/views/news/NewsList.vue')
    }
  ]
})

describe('NewsDetail 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(NewsDetail, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              news: {
                currentNews: mockNews,
                loading: false,
                error: null
              }
            }
          }),
          router
        ]
      }
    })
  }

  it('应该显示加载状态', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    store.$patch({ loading: true })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-test="loading-skeleton"]').exists()).toBe(true)
  })

  it('应该显示错误信息', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    store.$patch({ error: '获取新闻失败' })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-test="error-alert"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('获取新闻失败')
  })

  it('应该显示新闻不存在提示', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    store.$patch({ currentNews: null })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-test="not-found"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('新闻不存在')
  })

  it('应该显示新闻详情', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain(mockNews.title)
    expect(wrapper.text()).toContain(mockNews.author)
    expect(wrapper.text()).toContain(mockNews.source)
    expect(wrapper.text()).toContain(mockNews.category)
    expect(wrapper.text()).toContain(mockNews.content)
  })

  it('应该能编辑新闻', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    const editButton = wrapper.find('[data-test="edit-button"]')
    await editButton.trigger('click')

    expect(wrapper.find('[data-test="edit-dialog"]').exists()).toBe(true)

    const titleInput = wrapper.find('[data-test="edit-title"]')
    await titleInput.setValue('新标题')

    const submitButton = wrapper.find('[data-test="submit-edit"]')
    await submitButton.trigger('click')

    expect(store.updateNews).toHaveBeenCalledWith({
      ...mockNews,
      title: '新标题'
    })
  })

  it('应该能删除新闻', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm')
    
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    const deleteButton = wrapper.find('[data-test="delete-button"]')
    await deleteButton.trigger('click')

    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(store.deleteNews).toHaveBeenCalledWith(mockNews.id)
    expect(router.currentRoute.value.path).toBe('/news')
  })

  it('应该能返回列表', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    const backButton = wrapper.find('[data-test="back-button"]')
    await backButton.trigger('click')

    expect(router.currentRoute.value.path).toBe('/news')
  })
}) 