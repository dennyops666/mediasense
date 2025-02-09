import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import CrawlerList from '@/views/crawler/CrawlerList.vue'
import CrawlerConfig from '@/views/crawler/CrawlerConfig.vue'
import CrawlerData from '@/views/crawler/CrawlerData.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage, ElMessageBox } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('爬虫管理集成测试', () => {
  let router: any
  let store: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/crawler/list',
          name: 'CrawlerList',
          component: CrawlerList
        },
        {
          path: '/crawler/config/:id?',
          name: 'CrawlerConfig',
          component: CrawlerConfig
        },
        {
          path: '/crawler/data',
          name: 'CrawlerData',
          component: CrawlerData
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          tasks: [],
          configs: [],
          data: [],
          loading: false
        }
      }
    })

    store = useCrawlerStore()
  })

  describe('爬虫配置管理', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(CrawlerConfig, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })],
          stubs: {
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-button': true
          }
        }
      })
    })

    it('应该能创建新的爬虫配置', async () => {
      const form = wrapper.find('[data-test="config-form"]')
      const nameInput = wrapper.find('[data-test="config-name"]')
      const typeSelect = wrapper.find('[data-test="config-type"]')
      const urlInput = wrapper.find('[data-test="config-url"]')

      await nameInput.setValue('测试爬虫')
      await typeSelect.setValue('news')
      await urlInput.setValue('http://example.com')
      await form.trigger('submit')

      expect(store.createConfig).toHaveBeenCalledWith({
        name: '测试爬虫',
        type: 'news',
        url: 'http://example.com'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
      expect(router.currentRoute.value.path).toBe('/crawler/list')
    })

    it('应该能编辑现有爬虫配置', async () => {
      const mockConfig = {
        id: '1',
        name: '原始爬虫',
        type: 'news',
        url: 'http://example.com'
      }

      store.fetchConfigById.mockResolvedValue(mockConfig)
      await router.push('/crawler/config/1')

      const form = wrapper.find('[data-test="config-form"]')
      const nameInput = wrapper.find('[data-test="config-name"]')
      await nameInput.setValue('更新的爬虫')
      await form.trigger('submit')

      expect(store.updateConfig).toHaveBeenCalledWith('1', {
        ...mockConfig,
        name: '更新的爬虫'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
    })

    it('应该验证配置表单', async () => {
      const form = wrapper.find('[data-test="config-form"]')
      await form.trigger('submit')

      const errors = wrapper.findAll('.el-form-item__error')
      expect(errors.length).toBeGreaterThan(0)
      expect(store.createConfig).not.toHaveBeenCalled()
    })
  })

  describe('爬虫任务管理', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(CrawlerList, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })],
          stubs: {
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-tag': true
          }
        }
      })
    })

    it('应该能启动爬虫任务', async () => {
      const startButton = wrapper.find('[data-test="start-task-1"]')
      await startButton.trigger('click')

      expect(store.startTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已启动')
    })

    it('应该能停止爬虫任务', async () => {
      const stopButton = wrapper.find('[data-test="stop-task-1"]')
      await stopButton.trigger('click')

      expect(store.stopTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已停止')
    })

    it('应该能删除爬虫任务', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
      
      const deleteButton = wrapper.find('[data-test="delete-task-1"]')
      await deleteButton.trigger('click')

      expect(store.deleteTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('任务已删除')
    })

    it('应该能批量操作任务', async () => {
      const checkboxes = wrapper.findAll('[data-test="task-checkbox"]')
      await checkboxes[0].setChecked()
      await checkboxes[1].setChecked()

      const batchStartButton = wrapper.find('[data-test="batch-start"]')
      await batchStartButton.trigger('click')

      expect(store.batchStartTasks).toHaveBeenCalledWith(['1', '2'])
      expect(ElMessage.success).toHaveBeenCalledWith('批量启动成功')
    })
  })

  describe('爬虫数据管理', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(CrawlerData, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })],
          stubs: {
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-pagination': true
          }
        }
      })
    })

    it('应该能查看数据详情', async () => {
      const viewButton = wrapper.find('[data-test="view-data-1"]')
      await viewButton.trigger('click')

      const dialog = wrapper.find('[data-test="data-detail-dialog"]')
      expect(dialog.isVisible()).toBe(true)
    })

    it('应该能删除数据', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
      
      const deleteButton = wrapper.find('[data-test="delete-data-1"]')
      await deleteButton.trigger('click')

      expect(store.deleteData).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该能导出数据', async () => {
      const exportButton = wrapper.find('[data-test="export-button"]')
      await exportButton.trigger('click')

      expect(store.exportData).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('导出成功')
    })

    it('应该能筛选数据', async () => {
      const searchInput = wrapper.find('[data-test="data-search"]')
      await searchInput.setValue('测试数据')
      await searchInput.trigger('input')

      expect(store.fetchData).toHaveBeenCalledWith(
        expect.objectContaining({
          keyword: '测试数据'
        })
      )
    })
  })

  describe('错误处理', () => {
    it('应该处理配置创建失败', async () => {
      store.createConfig.mockRejectedValue(new Error('创建失败'))
      
      const wrapper = mount(CrawlerConfig, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await wrapper.find('[data-test="config-form"]').trigger('submit')
      expect(ElMessage.error).toHaveBeenCalledWith('创建失败')
    })

    it('应该处理任务操作失败', async () => {
      store.startTask.mockRejectedValue(new Error('启动失败'))
      
      const wrapper = mount(CrawlerList, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await wrapper.find('[data-test="start-task-1"]').trigger('click')
      expect(ElMessage.error).toHaveBeenCalledWith('启动失败')
    })

    it('应该处理数据导出失败', async () => {
      store.exportData.mockRejectedValue(new Error('导出失败'))
      
      const wrapper = mount(CrawlerData, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await wrapper.find('[data-test="export-button"]').trigger('click')
      expect(ElMessage.error).toHaveBeenCalledWith('导出失败')
    })
  })

  describe('状态同步', () => {
    it('应该在任务状态变化时更新列表', async () => {
      const wrapper = mount(CrawlerList, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await store.startTask('1')
      expect(store.fetchTasks).toHaveBeenCalled()
    })

    it('应该在数据变化时更新统计信息', async () => {
      const wrapper = mount(CrawlerData, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await store.deleteData('1')
      expect(store.fetchStats).toHaveBeenCalled()
    })
  })
}) 