import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import NewsDetail from '@/views/news/NewsDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createRouter, createWebHistory } from 'vue-router'
import { useNewsStore } from '@/stores/news'
import { nextTick, ref } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import {
  User,
  Link,
  Timer,
  Back,
  CollectionTag,
  Edit,
  Delete,
  View,
  Share
} from '@element-plus/icons-vue'
import { createTestingPinia } from '@pinia/testing'

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
    confirm: vi.fn().mockResolvedValue(true)
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

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/news/:id',
      name: 'NewsDetail',
      component: NewsDetail
    },
    {
      path: '/news',
      name: 'NewsList',
      component: { template: '<div>News List</div>' }
    }
  ]
})

// 添加router.push的spy
router.push = vi.fn()

describe('NewsDetail.vue', () => {
  let wrapper: any
  let store: any
  let router: any

  const createWrapper = async (options = {}) => {
    // 创建路由
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/news/list',
          name: 'NewsList',
          component: { template: '<div>News List</div>' }
        }
      ]
    })

    // 设置 pinia
    setActivePinia(createPinia())
    store = useNewsStore()

    // 设置初始状态
    await store.$patch({
      currentNews: options.currentNews ?? mockNewsDetail,
      loading: options.loading ?? false,
      error: options.error ?? null
    })

    // 等待 store 状态更新
    await nextTick()

    // 挂载组件
    wrapper = mount(NewsDetail, {
      global: {
        plugins: [
          router,
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              news: {
                currentNews: options.currentNews ?? mockNewsDetail,
                loading: options.loading ?? false,
                error: options.error ?? null
              }
            }
          })
        ],
        components: {
          User,
          Link,
          Timer,
          Back,
          CollectionTag,
          Edit,
          Delete,
          View,
          Share
        },
        stubs: {
          'el-card': {
            template: '<div class="el-card"><slot name="header"></slot><slot></slot></div>'
          },
          'el-button': {
            template: '<button class="el-button" :class="type ? `el-button--${type}` : \'\'" data-test="el-button" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['type'],
            emits: ['click']
          },
          'el-tag': {
            template: '<span class="el-tag" data-test="news-tag"><slot></slot></span>'
          },
          'el-skeleton': {
            template: '<div class="el-skeleton" data-test="loading-skeleton"><slot name="template"></slot></div>'
          },
          'el-skeleton-item': {
            template: '<div class="el-skeleton-item" :class="variant" data-test="skeleton-item"></div>',
            props: ['variant']
          },
          'el-alert': {
            template: '<div class="el-alert" data-test="error-alert"><slot></slot><div class="el-alert__title">{{ title }}</div></div>',
            props: ['title']
          },
          'el-empty': {
            template: '<div class="el-empty"><div class="el-empty__description">{{ description }}</div></div>',
            props: ['description']
          },
          'el-icon': {
            template: '<i class="el-icon"><slot></slot></i>'
          },
          'el-image': {
            template: '<img :src="src" class="el-image" data-test="news-image" />',
            props: ['src']
          },
          'el-dialog': {
            template: '<div class="el-dialog" data-test="edit-dialog" v-if="modelValue"><slot></slot><slot name="footer"></slot></div>',
            props: ['modelValue']
          },
          'el-form': {
            template: '<form class="el-form" data-test="edit-form"><slot></slot></form>',
            props: ['model']
          },
          'el-form-item': {
            template: '<div class="el-form-item"><label v-if="label">{{ label }}</label><slot></slot></div>',
            props: ['label']
          },
          'el-input': {
            template: '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-select': {
            template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['value', 'label']
          }
        }
      },
      props: {
        id: '1'
      }
    })

    // 等待组件更新完成
    await router.isReady()
    await nextTick()
    await wrapper.vm.$nextTick()
  }

  beforeEach(async () => {
    vi.clearAllMocks()
    await createWrapper()
  })

  it('应该在挂载时获取新闻详情', async () => {
    await wrapper.vm.$nextTick()
    expect(store.fetchNewsDetail).toHaveBeenCalledWith('1')
  })

  it('应该正确显示新闻详情', async () => {
    expect(wrapper.find('.news-title').text()).toBe(mockNewsDetail.title)
    expect(wrapper.find('.news-content').text()).toBe(mockNewsDetail.content)
    expect(wrapper.find('.news-source').text()).toBe(mockNewsDetail.source)
    expect(wrapper.find('.news-category').text()).toBe(mockNewsDetail.category)
  })

  it('应该显示发布时间', async () => {
    expect(wrapper.find('.meta-item:nth-child(2)').text()).toContain(mockNewsDetail.publishTime)
  })

  it('应该显示阅读量', async () => {
    expect(wrapper.find('.meta-item:last-child').text()).toContain(mockNewsDetail.views.toString())
  })

  it('应该能编辑新闻', async () => {
    const editButton = wrapper.find('[data-test="edit-button"]')
    expect(editButton.exists()).toBe(true)
    await editButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    const editDialog = wrapper.find('[data-test="edit-dialog"]')
    expect(editDialog.exists()).toBe(true)
  })

  it('应该能删除新闻', async () => {
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    expect(deleteButton.exists()).toBe(true)
    await deleteButton.trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    await wrapper.vm.$nextTick()
    expect(store.deleteNews).toHaveBeenCalledWith('1')
  })

  it('应该能返回列表页', async () => {
    const backButton = wrapper.find('.back-button')
    await backButton.trigger('click')
    
    expect(router.currentRoute.value.name).toBe('NewsList')
  })

  it('应该正确处理加载状态', async () => {
    store.$patch({ loading: true })
    await wrapper.vm.$nextTick()
    
    const skeleton = wrapper.find('[data-test="loading-skeleton"]')
    expect(skeleton.exists()).toBe(true)
  })

  it('应该正确处理错误状态', async () => {
    store.$patch({ error: '获取新闻详情失败' })
    await wrapper.vm.$nextTick()
    
    const errorMessage = wrapper.find('[data-test="error-alert"]')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('获取新闻详情失败')
  })

  it('应该在新闻不存在时显示提示', async () => {
    // 设置 pinia
    setActivePinia(createPinia())
    store = useNewsStore()
    
    // 设置初始状态
    await store.$patch({
      currentNews: null,
      loading: false,
      error: null
    })
    
    // 等待 store 状态更新
    await nextTick()
    
    // 创建组件
    wrapper = mount(NewsDetail, {
      global: {
        plugins: [router, createPinia()],
        components: {
          User,
          Link,
          Timer,
          Back,
          CollectionTag,
          Edit,
          Delete,
          View,
          Share
        },
        stubs: {
          'el-card': {
            template: '<div class="el-card"><slot name="header"></slot><slot></slot></div>'
          },
          'el-button': {
            template: '<button class="el-button" :class="type ? `el-button--${type}` : \'\'" data-test="el-button" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['type'],
            emits: ['click']
          },
          'el-tag': {
            template: '<span class="el-tag" data-test="news-tag"><slot></slot></span>'
          },
          'el-skeleton': {
            template: '<div class="el-skeleton" data-test="loading-skeleton"><slot name="template"></slot></div>'
          },
          'el-skeleton-item': {
            template: '<div class="el-skeleton-item" :class="variant" data-test="skeleton-item"></div>',
            props: ['variant']
          },
          'el-alert': {
            template: '<div class="el-alert" data-test="error-alert"><slot></slot><div class="el-alert__title">{{ title }}</div></div>',
            props: ['title']
          },
          'el-empty': {
            template: '<div class="el-empty"><div class="el-empty__description">{{ description }}</div></div>',
            props: ['description']
          },
          'el-icon': {
            template: '<i class="el-icon"><slot></slot></i>'
          },
          'el-image': {
            template: '<img :src="src" class="el-image" data-test="news-image" />',
            props: ['src']
          },
          'el-dialog': {
            template: '<div class="el-dialog" data-test="edit-dialog" v-if="modelValue"><slot></slot><slot name="footer"></slot></div>',
            props: ['modelValue']
          },
          'el-form': {
            template: '<form class="el-form" data-test="edit-form"><slot></slot></form>',
            props: ['model']
          },
          'el-form-item': {
            template: '<div class="el-form-item"><label v-if="label">{{ label }}</label><slot></slot></div>',
            props: ['label']
          },
          'el-input': {
            template: '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-select': {
            template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue'],
            emits: ['update:modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['value', 'label']
          }
        }
      },
      props: {
        id: '1'
      }
    })
    
    // 等待组件更新
    await nextTick()
    await wrapper.vm.$nextTick()
    
    // 打印调试信息
    console.log('Store state:', {
      currentNews: store.currentNews,
      loading: store.loading,
      error: store.error
    })
    
    console.log('Component HTML:', wrapper.html())
    
    const notFoundContainer = wrapper.find('.not-found')
    expect(notFoundContainer.exists()).toBe(true)
    
    const emptyComponent = wrapper.find('.el-empty')
    expect(emptyComponent.exists()).toBe(true)
    expect(emptyComponent.find('.el-empty__description').text()).toBe('新闻不存在')
  })

  it('应该显示新闻来源', async () => {
    expect(wrapper.find('.news-source').text()).toBe(mockNewsDetail.source)
  })

  it('应该显示新闻图片', async () => {
    const image = wrapper.find('[data-test="news-image"]')
    expect(image.exists()).toBe(true)
    expect(image.attributes('src')).toBe(mockNewsDetail.imageUrl)
  })

  it('应该能收藏新闻', async () => {
    const favoriteButton = wrapper.find('.favorite-button')
    await favoriteButton.trigger('click')
    
    expect(store.toggleFavorite).toHaveBeenCalledWith(mockNewsDetail.id)
    expect(ElMessage.success).toHaveBeenCalledWith('收藏成功')
  })

  it('应该能分享新闻', async () => {
    const shareButton = wrapper.find('.share-button')
    await shareButton.trigger('click')
    
    expect(ElMessage.success).toHaveBeenCalledWith('链接已复制到剪贴板')
  })
}) 