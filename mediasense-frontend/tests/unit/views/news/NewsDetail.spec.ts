import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import NewsDetail from '@/views/news/NewsDetail.vue'
import { useNewsStore } from '@/stores/news'
import { createRouter, createWebHistory } from 'vue-router'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() }
      },
      get: vi.fn().mockResolvedValue({ data: {} }),
      post: vi.fn().mockResolvedValue({ data: {} }),
      put: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      defaults: {
        headers: {
          common: {},
          get: {},
          post: {},
          put: {},
          delete: {}
        },
        timeout: 0,
        baseURL: ''
      }
    }))
  }
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined)
  }
})

// Mock data
const mockNewsDetail = {
  id: '1',
  title: '测试新闻标题',
  content: '测试新闻内容',
  author: '测试作者',
  publishTime: '2024-03-20',
  category: '测试分类',
  tags: ['标签1', '标签2'],
  source: '测试来源',
  imageUrl: 'test-image.jpg',
  views: 100,
  isFavorite: false
}

const mockStore = {
  currentNews: mockNewsDetail,
  loading: false,
  error: null,
  fetchNewsDetail: vi.fn().mockResolvedValue(mockNewsDetail),
  updateNews: vi.fn().mockResolvedValue(true),
  deleteNews: vi.fn().mockResolvedValue(true),
  toggleFavorite: vi.fn().mockResolvedValue(true),
  $patch: vi.fn(function(state) {
    Object.assign(this, state)
  })
}

vi.mock('@/stores/news', () => ({
  useNewsStore: () => mockStore
}))

vi.mock('pinia', async () => {
  const actual = await vi.importActual('pinia')
  return {
    ...actual,
    storeToRefs: vi.fn((store) => ({
      currentNews: ref(store.currentNews),
      loading: ref(store.loading),
      error: ref(store.error)
    }))
  }
})

// Mock vue-router
const mockRouter = {
  push: vi.fn()
}
vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

describe('NewsDetail.vue', () => {
  let wrapper
  let store

  beforeEach(() => {
    // 重置所有 mock
    vi.clearAllMocks()

    // 创建测试 pinia store
    wrapper = mount(NewsDetail, {
      props: {
        id: '1'
      },
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              news: {
                currentNews: null,
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-skeleton': true,
          'el-skeleton-item': true,
          'el-alert': true,
          'el-empty': true,
          'el-card': true,
          'el-button': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-icon': true,
          'el-tag': true
        }
      }
    })

    store = useNewsStore()
  })

  it('显示加载状态', async () => {
    store.loading = true
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="loading-skeleton"]').exists()).toBe(true)
  })

  it('显示错误信息', async () => {
    store.error = '加载失败'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="error-alert"]').exists()).toBe(true)
  })

  it('显示新闻不存在提示', async () => {
    store.currentNews = null
    store.loading = false
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.not-found').exists()).toBe(true)
  })

  it('显示新闻详情', async () => {
    store.currentNews = {
      id: '1',
      title: '测试新闻',
      content: '测试内容',
      author: '测试作者',
      source: '测试来源',
      publishTime: '2024-01-01',
      views: 100,
      tags: ['标签1', '标签2']
    }
    await wrapper.vm.$nextTick()
    
    // 使用 wrapper.text() 来检查文本内容
    const content = wrapper.text()
    expect(content).toContain('测试新闻')
    expect(content).toContain('测试来源')
    expect(wrapper.findAll('[data-test="news-tag"]')).toHaveLength(2)
  })

  it('编辑新闻', async () => {
    store.currentNews = {
      id: '1',
      title: '测试新闻',
      content: '测试内容',
      author: '测试作者',
      source: '测试来源'
    }
    await wrapper.vm.$nextTick()
    
    const editButton = wrapper.find('[data-test="edit-button"]')
    await editButton.trigger('click')
    expect(wrapper.find('[data-test="edit-dialog"]').exists()).toBe(true)
  })

  it('删除新闻', async () => {
    store.currentNews = {
      id: '1',
      title: '测试新闻'
    }
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
    
    await wrapper.vm.$nextTick()
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    await deleteButton.trigger('click')
    
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(store.deleteNews).toHaveBeenCalledWith('1')
  })

  it('返回列表', async () => {
    await wrapper.find('[data-test="back-button"]').trigger('click')
    expect(mockRouter.push).toHaveBeenCalledWith({ name: 'NewsList' })
  })
})