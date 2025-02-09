import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CrawlerList from '@/views/crawler/CrawlerList.vue'
import { useCrawlerStore } from '@/stores/crawler'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { inject } from 'vue'
import axios from 'axios'

// 模拟 Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue(true),
    alert: vi.fn().mockResolvedValue(true)
  },
  vLoading: {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
}))

// 模拟图标组件
vi.mock('@element-plus/icons-vue', () => {
  const createIconComponent = (name) => ({
    name,
    render: () => null
  })

  const icons = [
    'Plus',
    'VideoPlay',
    'Edit',
    'Delete',
    'Close',
    'Loading',
    'Search',
    'User',
    'CircleClose',
    'ArrowDown',
    'Lock',
    'Message',
    'Connection',
    'SuccessFilled',
    'WarningFilled',
    'CircleCheckFilled',
    'InfoFilled',
    'CircleCloseFilled',
    'QuestionFilled',
    'View',
    'Hide',
    'Minus',
    'Refresh',
    'Setting',
    'ArrowUp',
    'ArrowLeft',
    'ArrowRight',
    'CircleCheck',
    'Warning',
    'Info',
    'Question',
    'Success',
    'Error',
    'Star',
    'StarFilled',
    'Calendar',
    'Document',
    'Folder',
    'FolderOpened',
    'Timer',
    'Clock',
    'More',
    'Menu',
    'Check',
    'MoreFilled',
    'CaretTop',
    'CaretBottom',
    'DArrowLeft',
    'DArrowRight',
    'Switch'
  ]

  return icons.reduce((acc, name) => {
    acc[name] = createIconComponent(name)
    return acc
  }, {})
})

// 模拟数据
const mockConfigs = [
  {
  id: '1',
    name: '测试配置1',
    siteName: '测试网站1',
    siteUrl: 'https://test1.com',
    frequency: 60,
    enabled: true,
    lastRunTime: '2024-03-15T10:00:00Z'
  },
  {
    id: '2',
    name: '测试配置2',
    siteName: '测试网站2',
    siteUrl: 'https://test2.com',
    frequency: 1440,
    enabled: false,
    lastRunTime: null
  }
]

vi.mock('axios')

describe('CrawlerList.vue', () => {
  let wrapper
  let store

  beforeEach(async () => {
    // 重置所有模拟函数
    vi.clearAllMocks()
    
    // 创建测试 store
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        crawler: {
          configs: mockConfigs,
          loading: false,
          crawlers: [
            {
              id: 1,
              name: '测试爬虫1',
              url: 'http://test1.com',
              schedule: '0 0 * * *',
              status: 'active',
              lastRunTime: '2024-01-01 00:00:00',
              nextRunTime: '2024-01-02 00:00:00'
            },
            {
              id: 2,
              name: '测试爬虫2',
              url: 'http://test2.com',
              schedule: '0 12 * * *',
              status: 'inactive',
              lastRunTime: '2024-01-01 12:00:00',
              nextRunTime: '2024-01-02 12:00:00'
            }
          ],
          error: null
        }
      }
    })
    
    store = useCrawlerStore()
    
    // Mock store methods
    store.toggleConfig = vi.fn()
    store.runConfig = vi.fn()
    store.deleteConfig = vi.fn()
    store.createConfig = vi.fn()
    store.updateConfig = vi.fn()
    
    // 创建组件
    wrapper = mount(CrawlerList, {
      global: {
        plugins: [pinia],
        directives: {
          loading: {
            mounted: vi.fn(),
            updated: vi.fn(),
            unmounted: vi.fn()
          }
        },
        provide: {
          crawlerStore: store
        },
        stubs: {
          'el-button': {
            template: '<button class="el-button" :class="type" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['type']
          },
          'el-table': {
            template: '<div class="el-table"><slot></slot></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot></slot></div>'
          },
          'el-switch': {
            template: '<div class="el-switch" :class="{ \'is-checked\': modelValue }" @click="$emit(\'update:modelValue\', !modelValue)"></div>',
            props: ['modelValue']
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot></slot><slot name="footer"></slot></div>',
            props: ['modelValue']
          },
          'el-form': {
            template: '<form class="el-form" @submit.prevent><slot></slot></form>'
          },
          'el-form-item': {
            template: '<div class="el-form-item"><slot></slot></div>'
          },
          'el-input': {
            template: '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue']
          },
          'el-select': {
            template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['value', 'label']
          },
          'el-tag': {
            template: '<span class="el-tag" :class="type"><slot></slot></span>',
            props: ['type']
          }
        }
      }
    })

    await nextTick()
  })

  describe('基础渲染', () => {
    it('应该正确渲染爬虫配置列表', () => {
      const table = wrapper.find('.el-table')
      expect(table.exists()).toBe(true)
    })

    it('应该显示新建配置按钮', () => {
      const addButton = wrapper.find('.el-button--primary')
      expect(addButton.exists()).toBe(true)
    })
  })

  describe('数据展示', () => {
    it('应该正确格式化抓取频率', () => {
      const frequencyText = wrapper.find('[data-test="frequency-text"]')
      expect(frequencyText.exists()).toBe(true)
      expect(frequencyText.text()).toContain('1小时')
    })

    it('应该正确显示上次运行时间', () => {
      const lastRunText = wrapper.find('[data-test="last-run-text"]')
      expect(lastRunText.exists()).toBe(true)
      expect(lastRunText.text()).toContain('2024-03-15')
    })
  })

  describe('操作功能', () => {
    it('应该能够切换爬虫状态', async () => {
      const switchComponent = wrapper.find('.el-switch')
      expect(switchComponent.exists()).toBe(true)
      await switchComponent.trigger('click')
      expect(store.toggleConfig).toHaveBeenCalledWith('1', false)
    })

    it('应该能够立即运行爬虫', async () => {
      const runButton = wrapper.find('.el-button--primary')
      expect(runButton.exists()).toBe(true)
      await runButton.trigger('click')
      expect(store.runConfig).toHaveBeenCalled()
    })

    it('应该能够编辑配置', async () => {
      const editButton = wrapper.find('.el-button--warning')
      expect(editButton.exists()).toBe(true)
      await editButton.trigger('click')
      
      const form = wrapper.find('.el-form')
      expect(form.exists()).toBe(true)
    })

    it('应该能够删除配置', async () => {
      const deleteButton = wrapper.find('.el-button--danger')
      expect(deleteButton.exists()).toBe(true)
      await deleteButton.trigger('click')
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(store.deleteConfig).toHaveBeenCalled()
    })
  })

  describe('表单操作', () => {
    it('应该验证必填字段', async () => {
      // 打开创建表单
      await wrapper.find('.el-button--primary').trigger('click')
      
      const form = wrapper.find('.el-form')
      expect(form.exists()).toBe(true)
      
      // 尝试提交空表单
      await form.trigger('submit')
      
      // 验证输入框存在
      const nameInput = wrapper.find('.el-input[name="name"]')
      const siteNameInput = wrapper.find('.el-input[name="site-name"]')
      const siteUrlInput = wrapper.find('.el-input[name="site-url"]')
      const frequencyInput = wrapper.find('.el-input[name="frequency"]')
      
      expect(nameInput.exists()).toBe(true)
      expect(siteNameInput.exists()).toBe(true)
      expect(siteUrlInput.exists()).toBe(true)
      expect(frequencyInput.exists()).toBe(true)
    })
  })

  describe('加载状态', () => {
    it('应该在操作时禁用按钮', async () => {
      store.$patch({ loading: true })
      await nextTick()
      
      const buttons = wrapper.findAll('.el-button')
      buttons.forEach(button => {
        expect(button.attributes('disabled')).toBe('true')
      })
    })
  })

  describe('错误处理', () => {
    it('应该处理删除失败的情况', async () => {
      store.deleteConfig.mockRejectedValueOnce(new Error('删除失败'))
      
      const deleteButton = wrapper.find('.el-button--danger')
      expect(deleteButton.exists()).toBe(true)
      await deleteButton.trigger('click')
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(store.deleteConfig).toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
    })
  })

  describe('爬虫操作', () => {
    it('应该能打开添加爬虫对话框', async () => {
      await wrapper.find('.el-button--primary').trigger('click')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该能提交添加爬虫表单', async () => {
      const newCrawler = {
        name: '新爬虫',
        url: 'http://test.com',
        schedule: '0 0 * * *'
      }

      vi.mocked(axios.post).mockResolvedValueOnce({ data: { ...newCrawler, id: 3 } })

      wrapper.vm.crawlerForm = newCrawler
      await wrapper.vm.handleSubmit()

      expect(axios.post).toHaveBeenCalledWith('/api/crawlers', newCrawler)
      expect(ElMessage.success).toHaveBeenCalled()
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('应该能启动爬虫', async () => {
      vi.mocked(axios.post).mockResolvedValueOnce({ data: { message: '爬虫已启动' } })
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce()

      await wrapper.vm.handleStart(wrapper.vm.crawlers[1])

      expect(axios.post).toHaveBeenCalledWith('/api/crawlers/2/start')
      expect(ElMessage.success).toHaveBeenCalled()
    })

    it('应该能停止爬虫', async () => {
      vi.mocked(axios.post).mockResolvedValueOnce({ data: { message: '爬虫已停止' } })
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce()

      await wrapper.vm.handleStop(wrapper.vm.crawlers[0])

      expect(axios.post).toHaveBeenCalledWith('/api/crawlers/1/stop')
      expect(ElMessage.success).toHaveBeenCalled()
    })

    it('应该能删除爬虫', async () => {
      vi.mocked(axios.delete).mockResolvedValueOnce({ data: { message: '爬虫已删除' } })
      vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce()

      await wrapper.vm.handleDelete(wrapper.vm.crawlers[0])

      expect(axios.delete).toHaveBeenCalledWith('/api/crawlers/1')
      expect(ElMessage.success).toHaveBeenCalled()
    })

    it('应该能编辑爬虫', async () => {
      const updatedCrawler = {
        ...wrapper.vm.crawlers[0],
        name: '更新后的爬虫',
        url: 'http://updated.com'
      }

      vi.mocked(axios.put).mockResolvedValueOnce({ data: updatedCrawler })

      wrapper.vm.crawlerForm = updatedCrawler
      wrapper.vm.editingCrawlerId = 1
      await wrapper.vm.handleSubmit()

      expect(axios.put).toHaveBeenCalledWith('/api/crawlers/1', updatedCrawler)
      expect(ElMessage.success).toHaveBeenCalled()
      expect(wrapper.vm.dialogVisible).toBe(false)
    })

    it('应该能处理表单验证错误', async () => {
      wrapper.vm.crawlerForm = {
        name: '',
        url: 'invalid-url',
        schedule: ''
      }

      await wrapper.vm.handleSubmit()
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('应该能处理API错误', async () => {
      const error = new Error('API错误')
      vi.mocked(axios.post).mockRejectedValueOnce(error)

      wrapper.vm.crawlerForm = {
        name: '新爬虫',
        url: 'http://test.com',
        schedule: '0 0 * * *'
      }

      await wrapper.vm.handleSubmit()
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })
}) 