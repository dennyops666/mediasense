import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import CrawlerConfigForm from '@/components/crawler/CrawlerConfigForm.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { ElMessage } from 'element-plus'
import type { CrawlerConfig } from '@/types/crawler'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('CrawlerConfigForm.vue', () => {
  const mockConfig: CrawlerConfig = {
    id: '1',
    name: '测试配置',
    type: 'news',
    url: 'http://example.com',
    enabled: true,
    targetUrl: 'http://example.com',
    method: 'GET',
    headers: [],
    selectors: [
      { field: 'title', selector: '.title', type: 'css' }
    ],
    timeout: 30,
    retries: 3,
    concurrency: 1,
    selector: {
      title: '.title',
      content: '.content'
    },
    userAgent: 'Mozilla/5.0'
  }

  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          currentConfig: mockConfig,
          loading: false
        }
      }
    })

    wrapper = mount(CrawlerConfigForm, {
      props: {
        initialConfig: mockConfig,
        mode: 'edit'
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-button': true
        }
      }
    })

    store = useCrawlerStore()
  })

  describe('表单渲染', () => {
    it('应该正确渲染表单字段', () => {
      const nameInput = wrapper.find('[data-test="crawler-name"]')
      const typeSelect = wrapper.find('[data-test="crawler-type"]')
      const urlInput = wrapper.find('[data-test="crawler-url"]')
      const methodSelect = wrapper.find('[data-test="crawler-method"]')
      
      expect(nameInput.exists()).toBe(true)
      expect(typeSelect.exists()).toBe(true)
      expect(urlInput.exists()).toBe(true)
      expect(methodSelect.exists()).toBe(true)
    })

    it('应该显示初始配置数据', () => {
      const form = wrapper.vm.formData
      expect(form.name).toBe('测试配置')
      expect(form.type).toBe('news')
      expect(form.url).toBe('http://example.com')
      expect(form.method).toBe('GET')
    })

    it('应该显示选择器列表', () => {
      const selectorItems = wrapper.findAll('[data-test="selector-item"]')
      expect(selectorItems).toHaveLength(1)
      expect(selectorItems[0].find('input[placeholder="字段名"]').element.value).toBe('title')
    })
  })

  describe('表单操作', () => {
    it('应该能添加选择器', async () => {
      const addButton = wrapper.find('[data-test="add-selector"]')
      await addButton.trigger('click')

      const selectorItems = wrapper.findAll('[data-test="selector-item"]')
      expect(selectorItems).toHaveLength(2)
    })

    it('应该能删除选择器', async () => {
      const deleteButton = wrapper.find('[data-test="delete-selector"]')
      await deleteButton.trigger('click')

      const selectorItems = wrapper.findAll('[data-test="selector-item"]')
      expect(selectorItems).toHaveLength(0)
    })

    it('应该能重置表单', async () => {
      const resetButton = wrapper.find('[data-test="reset-button"]')
      await resetButton.trigger('click')

      const form = wrapper.vm.formData
      expect(form.name).toBe('')
      expect(form.type).toBe('news')
      expect(form.url).toBe('')
    })

    it('应该能测试配置', async () => {
      const testButton = wrapper.find('[data-test="test-button"]')
      await testButton.trigger('click')

      expect(store.testConfig).toHaveBeenCalledWith(wrapper.vm.formData)
      expect(ElMessage.success).toHaveBeenCalledWith('测试成功')
    })
  })

  describe('表单提交', () => {
    it('创建模式下应该能提交新配置', async () => {
      await wrapper.setProps({ mode: 'create' })
      
      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(store.createConfig).toHaveBeenCalledWith(wrapper.vm.formData)
      expect(ElMessage.success).toHaveBeenCalledWith('创建爬虫配置成功')
    })

    it('编辑模式下应该能更新配置', async () => {
      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(store.updateConfig).toHaveBeenCalledWith('1', wrapper.vm.formData)
      expect(ElMessage.success).toHaveBeenCalledWith('更新配置成功')
    })
  })

  describe('表单验证', () => {
    it('应该验证必填字段', async () => {
      await wrapper.setData({
        formData: {
          name: '',
          type: '',
          url: '',
          method: ''
        }
      })

      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(store.createConfig).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('表单验证失败')
    })

    it('应该验证URL格式', async () => {
      await wrapper.setData({
        formData: {
          ...mockConfig,
          url: 'invalid-url'
        }
      })

      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(store.createConfig).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('表单验证失败')
    })
  })

  describe('错误处理', () => {
    it('应该处理创建失败', async () => {
      await wrapper.setProps({ mode: 'create' })
      store.createConfig.mockRejectedValue(new Error('创建失败'))

      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('表单验证失败')
    })

    it('应该处理更新失败', async () => {
      store.updateConfig.mockRejectedValue(new Error('更新失败'))

      const submitButton = wrapper.find('[data-test="submit-button"]')
      await submitButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('表单验证失败')
    })

    it('应该处理测试失败', async () => {
      store.testConfig.mockRejectedValue(new Error('测试失败'))

      const testButton = wrapper.find('[data-test="test-button"]')
      await testButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('测试失败')
    })
  })
}) 