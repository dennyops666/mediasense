import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import AIKeywordsCloud from '@/components/ai/AIKeywordsCloud.vue'
import { useAIStore } from '@/stores/ai'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

describe('AIKeywordsCloud.vue', () => {
  const mockKeywords = [
    { name: '人工智能', value: 100 },
    { name: '机器学习', value: 85 },
    { name: '深度学习', value: 70 },
    { name: '神经网络', value: 65 },
    { name: '数据分析', value: 60 }
  ]

  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        ai: {
          keywords: mockKeywords,
          loading: false
        }
      }
    })

    wrapper = mount(AIKeywordsCloud, {
      props: {
        width: 800,
        height: 400,
        minFontSize: 12,
        maxFontSize: 60,
        colors: ['#1f77b4', '#ff7f0e', '#2ca02c']
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'el-skeleton': true
        }
      }
    })

    store = useAIStore()
  })

  describe('组件初始化', () => {
    it('应该正确初始化图表', () => {
      expect(echarts.init).toHaveBeenCalled()
      expect(wrapper.vm.chart).toBeTruthy()
    })

    it('应该使用正确的配置初始化', () => {
      const chartInstance = wrapper.vm.chart
      expect(chartInstance.setOption).toHaveBeenCalledWith(
        expect.objectContaining({
          series: expect.arrayContaining([
            expect.objectContaining({
              type: 'wordCloud',
              shape: 'circle'
            })
          ])
        })
      )
    })

    it('应该响应属性变化', async () => {
      await wrapper.setProps({ width: 1000 })
      expect(wrapper.vm.chart.resize).toHaveBeenCalled()
    })
  })

  describe('数据加载', () => {
    it('应该显示加载状态', async () => {
      await wrapper.setData({ loading: true })
      const loading = wrapper.find('[data-test="loading"]')
      expect(loading.exists()).toBe(true)
    })

    it('应该处理加载错误', async () => {
      await wrapper.setData({ error: '加载失败' })
      const error = wrapper.find('[data-test="error"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该加载关键词数据', async () => {
      expect(store.fetchKeywords).toHaveBeenCalledWith('24h')
      const chartInstance = wrapper.vm.chart
      expect(chartInstance.setOption).toHaveBeenCalledWith(
        expect.objectContaining({
          series: expect.arrayContaining([
            expect.objectContaining({
              data: expect.arrayContaining([
                expect.objectContaining({
                  name: '人工智能',
                  value: 100
                })
              ])
            })
          ])
        })
      )
    })
  })

  describe('时间范围选择', () => {
    it('应该能切换时间范围', async () => {
      const select = wrapper.find('[data-test="time-range-select"]')
      await select.setValue('7d')
      await select.trigger('change')

      expect(store.fetchKeywords).toHaveBeenCalledWith('7d')
    })

    it('应该在切换时间范围后更新图表', async () => {
      const select = wrapper.find('[data-test="time-range-select"]')
      await select.setValue('30d')
      await select.trigger('change')

      const chartInstance = wrapper.vm.chart
      expect(chartInstance.setOption).toHaveBeenCalled()
    })
  })

  describe('刷新功能', () => {
    it('应该能手动刷新数据', async () => {
      const refreshButton = wrapper.find('[data-test="refresh-button"]')
      await refreshButton.trigger('click')

      expect(store.fetchKeywords).toHaveBeenCalled()
    })

    it('应该在刷新时显示加载状态', async () => {
      const refreshButton = wrapper.find('[data-test="refresh-button"]')
      await wrapper.setData({ loading: true })
      
      expect(refreshButton.attributes('loading')).toBe('true')
    })
  })

  describe('图表交互', () => {
    it('应该响应窗口大小变化', async () => {
      window.dispatchEvent(new Event('resize'))
      expect(wrapper.vm.chart.resize).toHaveBeenCalled()
    })

    it('应该在组件卸载时清理图表实例', () => {
      const chartInstance = wrapper.vm.chart
      wrapper.unmount()
      expect(chartInstance.dispose).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该处理数据获取失败', async () => {
      store.fetchKeywords.mockRejectedValue(new Error('获取关键词失败'))
      
      const refreshButton = wrapper.find('[data-test="refresh-button"]')
      await refreshButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('获取关键词失败')
      expect(wrapper.vm.error).toBe('获取关键词失败')
    })

    it('应该显示重试按钮', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const retryButton = wrapper.find('[data-test="retry-button"]')
      expect(retryButton.exists()).toBe(true)
      
      await retryButton.trigger('click')
      expect(store.fetchKeywords).toHaveBeenCalled()
    })
  })

  describe('自定义配置', () => {
    it('应该应用自定义颜色', () => {
      const colors = ['#ff0000', '#00ff00', '#0000ff']
      wrapper = mount(AIKeywordsCloud, {
        props: {
          width: 800,
          height: 400,
          colors
        },
        global: {
          plugins: [createTestingPinia({ createSpy: vi.fn })]
        }
      })

      const chartInstance = wrapper.vm.chart
      expect(chartInstance.setOption).toHaveBeenCalledWith(
        expect.objectContaining({
          series: expect.arrayContaining([
            expect.objectContaining({
              textStyle: expect.objectContaining({
                color: expect.any(Function)
              })
            })
          ])
        })
      )
    })

    it('应该应用自定义字体大小范围', () => {
      wrapper = mount(AIKeywordsCloud, {
        props: {
          width: 800,
          height: 400,
          minFontSize: 16,
          maxFontSize: 80
        },
        global: {
          plugins: [createTestingPinia({ createSpy: vi.fn })]
        }
      })

      const chartInstance = wrapper.vm.chart
      expect(chartInstance.setOption).toHaveBeenCalledWith(
        expect.objectContaining({
          series: expect.arrayContaining([
            expect.objectContaining({
              sizeRange: [16, 80]
            })
          ])
        })
      )
    })
  })
})
