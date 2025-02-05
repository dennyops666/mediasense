import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import CrawlerList from '@/views/crawler/CrawlerList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerConfig } from '@/types/crawler'
import { nextTick } from 'vue'

const mockCrawlerData: CrawlerConfig = {
  id: '1',
  name: '测试爬虫',
  siteName: '测试网站',
  siteUrl: 'http://test.com',
  frequency: 3600,
  isEnabled: true,
  lastRun: '2024-03-20T12:00:00Z',
  nextRun: '2024-03-20T13:00:00Z',
  errorCount: 0,
  lastError: null,
  configType: 'rss',
  useProxy: false
}

describe('CrawlerList.vue', () => {
  let wrapper
  let store
  let pinia

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    store = useCrawlerStore()
    
    // Mock store methods
    store.fetchConfigs = vi.fn().mockResolvedValue([mockCrawlerData])
    store.createConfig = vi.fn().mockResolvedValue(mockCrawlerData)
    store.updateConfig = vi.fn().mockResolvedValue(mockCrawlerData)
    store.deleteConfig = vi.fn().mockResolvedValue()
    store.toggleConfig = vi.fn().mockResolvedValue()
    store.runConfig = vi.fn().mockResolvedValue()

    // 提供初始数据
    const initialData = {
      configs: [mockCrawlerData],
      dialogVisible: false,
      dialogTitle: '',
      formData: {
        name: '',
        siteName: '',
        siteUrl: '',
        frequency: 3600,
        isEnabled: true,
        configType: 'rss',
        useProxy: false
      }
    }

    wrapper = mount(CrawlerList, {
      global: {
        plugins: [ElementPlus, pinia],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-input-number': true,
          'el-switch': true,
          'el-link': true
        }
      },
      data() {
        return initialData
      }
    })

    await nextTick()
  })

  describe('组件初始化', () => {
    it('应该在挂载时加载爬虫配置列表', async () => {
      expect(store.fetchConfigs).toHaveBeenCalled()
    })
  })

  describe('创建爬虫配置', () => {
    it('应该正确提交创建表单', async () => {
      const newConfig = {
        name: '新爬虫',
        siteName: '新网站',
        siteUrl: 'http://new.com',
        frequency: 7200,
        isEnabled: true,
        configType: 'rss',
        useProxy: false
      }

      await wrapper.setData({
        dialogVisible: true,
        dialogTitle: '创建爬虫配置',
        formData: newConfig
      })

      await wrapper.vm.handleSubmit()
      
      expect(store.createConfig).toHaveBeenCalledWith(newConfig)
    })
  })

  describe('编辑爬虫配置', () => {
    it('应该正确提交编辑表单', async () => {
      const updatedConfig = {
        ...mockCrawlerData,
        name: '更新的爬虫'
      }

      await wrapper.setData({
        dialogVisible: true,
        dialogTitle: '编辑爬虫配置',
        formData: updatedConfig
      })

      await wrapper.vm.handleSubmit()
      
      expect(store.updateConfig).toHaveBeenCalledWith(mockCrawlerData.id, updatedConfig)
    })
  })

  describe('删除爬虫配置', () => {
    it('应该正确处理删除操作', async () => {
      await wrapper.vm.handleDelete(mockCrawlerData.id)
      expect(store.deleteConfig).toHaveBeenCalledWith(mockCrawlerData.id)
    })
  })

  describe('切换爬虫状态', () => {
    it('应该正确处理状态切换', async () => {
      await wrapper.vm.handleToggleStatus(mockCrawlerData.id, !mockCrawlerData.isEnabled)
      expect(store.toggleConfig).toHaveBeenCalledWith(mockCrawlerData.id, !mockCrawlerData.isEnabled)
    })
  })

  describe('运行爬虫', () => {
    it('应该正确处理手动运行操作', async () => {
      await wrapper.vm.handleRun(mockCrawlerData.id)
      expect(store.runConfig).toHaveBeenCalledWith(mockCrawlerData.id)
    })
  })
}) 