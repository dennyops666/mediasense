import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import CrawlerList from '@/views/crawler/CrawlerList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage } from 'element-plus'
import ElementPlus from 'element-plus'
import axios from 'axios'

// 创建一个模拟的 axios 实例
const mockAxiosInstance = vi.hoisted(() => ({
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn()
    },
    response: {
      use: vi.fn(),
      eject: vi.fn()
    }
  },
  request: vi.fn()
}))

// 模拟 axios.create
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance)
  }
}))

// 模拟 Element Plus 消息组件
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/crawler',
      name: 'crawler-list',
      component: CrawlerList
    }
  ]
})

describe('爬虫管理流程集成测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
    router.push('/crawler')
  })

  const mountComponent = () => {
    return mount(CrawlerList, {
      global: {
        plugins: [
          ElementPlus,
          router,
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                configs: []
              }
            }
          })
        ],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-switch': true
        }
      }
    })
  }

  describe('爬虫配置管理', () => {
    it('应该完成爬虫配置的创建', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 模拟 API 响应
      mockAxiosInstance.request.mockResolvedValueOnce({
        data: {
          status: 'success',
          data: {
            id: '1',
            name: '测试爬虫',
            url: 'https://example.com',
            schedule: '0 0 * * *',
            selectors: {
              title: '.title',
              content: '.content'
            },
            status: 'active'
          }
        }
      })

      // 打开创建对话框
      await wrapper.find('[data-test="create-config-btn"]').trigger('click')

      // 填写表单
      await wrapper.find('[data-test="config-name"]').setValue('测试爬虫')
      await wrapper.find('[data-test="config-url"]').setValue('https://example.com')
      await wrapper.find('[data-test="config-schedule"]').setValue('0 0 * * *')
      await wrapper.find('[data-test="config-selector-title"]').setValue('.title')
      await wrapper.find('[data-test="config-selector-content"]').setValue('.content')

      // 提交表单
      await wrapper.find('[data-test="submit-config-btn"]').trigger('click')

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'post',
        url: '/crawler/configs',
        data: {
          name: '测试爬虫',
          url: 'https://example.com',
          schedule: '0 0 * * *',
          selectors: {
            title: '.title',
            content: '.content'
          }
        }
      })

      expect(ElMessage.success).toHaveBeenCalledWith('爬虫配置创建成功')
    })

    it('应该完成爬虫配置的编辑', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 设置初始状态
      store.$patch({
        configs: [{
          id: '1',
          name: '测试爬虫',
          url: 'https://example.com'
        }]
      })

      // 模拟 API 响应
      mockAxiosInstance.request.mockResolvedValueOnce({
        data: {
          status: 'success',
          data: {
            id: '1',
            name: '更新后的爬虫',
            url: 'https://example.com/new'
          }
        }
      })

      // 点击编辑按钮
      await wrapper.find('[data-test="edit-config-btn-1"]').trigger('click')

      // 修改表单
      await wrapper.find('[data-test="config-name"]').setValue('更新后的爬虫')
      await wrapper.find('[data-test="config-url"]').setValue('https://example.com/new')

      // 提交更新
      await wrapper.find('[data-test="update-config-btn"]').trigger('click')

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'put',
        url: '/crawler/configs/1',
        data: {
          name: '更新后的爬虫',
          url: 'https://example.com/new'
        }
      })

      expect(ElMessage.success).toHaveBeenCalledWith('爬虫配置更新成功')
    })

    it('应该完成爬虫配置的删除', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 设置初始状态
      store.$patch({
        configs: [{
          id: '1',
          name: '测试爬虫'
        }]
      })

      // 模拟 API 响应
      mockAxiosInstance.request.mockResolvedValueOnce({
        data: {
          status: 'success',
          data: { success: true }
        }
      })

      // 点击删除按钮
      await wrapper.find('[data-test="delete-config-btn-1"]').trigger('click')
      
      // 确认删除
      await wrapper.find('[data-test="confirm-delete-btn"]').trigger('click')

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'delete',
        url: '/crawler/configs/1'
      })

      expect(ElMessage.success).toHaveBeenCalledWith('爬虫配置删除成功')
    })
  })

  describe('爬虫运行管理', () => {
    it('应该正确启动爬虫任务', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 设置初始状态
      store.$patch({
        configs: [{
          id: '1',
          name: '测试爬虫',
          status: 'inactive'
        }]
      })

      // 模拟 API 响应
      mockAxiosInstance.request.mockResolvedValueOnce({
        data: {
          status: 'success',
          data: { status: 'running' }
        }
      })

      // 点击运行按钮
      await wrapper.find('[data-test="run-config-btn-1"]').trigger('click')

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'post',
        url: '/crawler/configs/1/run'
      })

      expect(ElMessage.success).toHaveBeenCalledWith('爬虫任务已启动')
    })

    it('应该正确停止爬虫任务', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 设置初始状态
      store.$patch({
        configs: [{
          id: '1',
          name: '测试爬虫',
          status: 'running'
        }]
      })

      // 模拟 API 响应
      mockAxiosInstance.request.mockResolvedValueOnce({
        data: {
          status: 'success',
          data: { status: 'stopped' }
        }
      })

      // 点击停止按钮
      await wrapper.find('[data-test="stop-config-btn-1"]').trigger('click')

      expect(mockAxiosInstance.request).toHaveBeenCalledWith({
        method: 'post',
        url: '/crawler/configs/1/stop'
      })

      expect(ElMessage.success).toHaveBeenCalledWith('爬虫任务已停止')
    })
  })

  describe('爬虫日志查看', () => {
    it('应该正确显示爬虫运行日志', async () => {
      const wrapper = mount(CrawlerList, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                crawler: {
                  configs: [
                    {
                      id: '1',
                      name: '测试爬虫'
                    }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const store = useCrawlerStore()
      const mockLogs = [
        { timestamp: '2024-03-20T10:00:00Z', level: 'info', message: '开始爬取' },
        { timestamp: '2024-03-20T10:01:00Z', level: 'success', message: '爬取完成' }
      ]

      vi.mocked(store.fetchLogs).mockResolvedValueOnce(mockLogs)

      // 点击查看日志按钮
      await wrapper.find('.view-logs-btn').trigger('click')

      expect(store.fetchLogs).toHaveBeenCalledWith('1')

      await wrapper.vm.$nextTick()

      // 验证日志显示
      const logItems = wrapper.findAll('.log-item')
      expect(logItems).toHaveLength(2)
      expect(logItems[0].text()).toContain('开始爬取')
      expect(logItems[1].text()).toContain('爬取完成')
    })
  })

  describe('错误处理', () => {
    it('应该正确处理配置验证错误', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 模拟 API 错误
      mockAxiosInstance.request.mockRejectedValueOnce({
        response: {
          data: {
            status: 'error',
            message: '配置验证失败'
          }
        }
      })

      // 打开创建对话框
      await wrapper.find('[data-test="create-config-btn"]').trigger('click')

      // 提交空表单
      await wrapper.find('[data-test="submit-config-btn"]').trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('配置验证失败')
    })

    it('应该正确处理运行失败', async () => {
      const wrapper = mountComponent()
      const store = useCrawlerStore()
      
      // 设置初始状态
      store.$patch({
        configs: [{
          id: '1',
          name: '测试爬虫',
          status: 'inactive'
        }]
      })

      // 模拟 API 错误
      mockAxiosInstance.request.mockRejectedValueOnce({
        response: {
          data: {
            status: 'error',
            message: '运行失败'
          }
        }
      })

      // 点击运行按钮
      await wrapper.find('[data-test="run-config-btn-1"]').trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('运行失败')
    })
  })
}) 