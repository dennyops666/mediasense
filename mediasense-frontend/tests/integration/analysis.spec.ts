import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import DataAnalysis from '@/views/analysis/DataAnalysis.vue'
import { useAnalysisStore } from '@/stores/analysis'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('数据分析集成测试', () => {
  let router: any
  let store: any
  let wrapper: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/analysis',
          component: DataAnalysis
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        analysis: {
          statistics: {
            total: 1000,
            today: 50,
            growth: 0.05
          },
          trends: [
            { date: '2024-03-01', value: 100 },
            { date: '2024-03-02', value: 120 }
          ],
          loading: false
        }
      }
    })

    wrapper = mount(DataAnalysis, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'el-card': true,
          'el-table': true,
          'el-chart': true
        }
      }
    })

    store = useAnalysisStore()
  })

  describe('数据统计分析', () => {
    it('应该显示数据统计概览', () => {
      const overview = wrapper.find('[data-test="data-overview"]')
      expect(overview.exists()).toBe(true)
      expect(overview.text()).toContain('1000')
      expect(overview.text()).toContain('50')
      expect(overview.text()).toContain('5%')
    })

    it('应该能按时间范围筛选数据', async () => {
      const datePicker = wrapper.find('[data-test="date-range"]')
      await datePicker.trigger('change', ['2024-03-01', '2024-03-02'])

      expect(store.fetchStatistics).toHaveBeenCalledWith({
        startDate: '2024-03-01',
        endDate: '2024-03-02'
      })
    })

    it('应该能按数据类型筛选', async () => {
      const typeSelect = wrapper.find('[data-test="data-type"]')
      await typeSelect.trigger('change', 'news')

      expect(store.fetchStatistics).toHaveBeenCalledWith({
        type: 'news'
      })
    })
  })

  describe('趋势图表展示', () => {
    it('应该正确渲染趋势图表', () => {
      const chart = wrapper.find('[data-test="trend-chart"]')
      expect(chart.exists()).toBe(true)
      expect(chart.attributes('data')).toBeTruthy()
    })

    it('应该支持切换图表类型', async () => {
      const chartTypeSwitch = wrapper.find('[data-test="chart-type"]')
      await chartTypeSwitch.trigger('change', 'bar')

      const chart = wrapper.find('[data-test="trend-chart"]')
      expect(chart.attributes('type')).toBe('bar')
    })

    it('应该能自动更新图表数据', async () => {
      vi.useFakeTimers()
      wrapper.vm.startAutoRefresh()
      
      vi.advanceTimersByTime(60000)
      expect(store.fetchTrends).toHaveBeenCalledTimes(2)
      
      vi.useRealTimers()
    })
  })

  describe('数据导出功能', () => {
    it('应该能导出统计数据', async () => {
      const exportButton = wrapper.find('[data-test="export-stats"]')
      await exportButton.trigger('click')

      expect(store.exportStatistics).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('数据导出成功')
    })

    it('应该能选择导出格式', async () => {
      const formatSelect = wrapper.find('[data-test="export-format"]')
      await formatSelect.trigger('change', 'excel')

      const exportButton = wrapper.find('[data-test="export-stats"]')
      await exportButton.trigger('click')

      expect(store.exportStatistics).toHaveBeenCalledWith({
        format: 'excel'
      })
    })

    it('应该处理导出失败的情况', async () => {
      store.exportStatistics.mockRejectedValue(new Error('导出失败'))
      
      const exportButton = wrapper.find('[data-test="export-stats"]')
      await exportButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('导出失败')
    })
  })

  describe('报表生成功能', () => {
    it('应该能生成分析报表', async () => {
      const generateButton = wrapper.find('[data-test="generate-report"]')
      await generateButton.trigger('click')

      expect(store.generateReport).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('报表生成成功')
    })

    it('应该能选择报表模板', async () => {
      const templateSelect = wrapper.find('[data-test="report-template"]')
      await templateSelect.trigger('change', 'monthly')

      const generateButton = wrapper.find('[data-test="generate-report"]')
      await generateButton.trigger('click')

      expect(store.generateReport).toHaveBeenCalledWith({
        template: 'monthly'
      })
    })

    it('应该能预览报表', async () => {
      const previewButton = wrapper.find('[data-test="preview-report"]')
      await previewButton.trigger('click')

      const preview = wrapper.find('[data-test="report-preview"]')
      expect(preview.exists()).toBe(true)
      expect(preview.isVisible()).toBe(true)
    })

    it('应该能下载报表', async () => {
      const downloadButton = wrapper.find('[data-test="download-report"]')
      await downloadButton.trigger('click')

      expect(store.downloadReport).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('报表下载成功')
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该能重试加载', async () => {
      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')

      expect(store.fetchStatistics).toHaveBeenCalled()
      expect(store.fetchTrends).toHaveBeenCalled()
    })
  })
}) 