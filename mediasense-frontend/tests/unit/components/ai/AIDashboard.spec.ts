import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import AIDashboard from '@/components/ai/AIDashboard.vue'
import { useAIStore } from '@/stores/ai'
import * as echarts from 'echarts'
import { nextTick } from 'vue'
import { vLoading } from 'element-plus'

const mockChartInstance = {
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  on: vi.fn(),
  off: vi.fn()
}

vi.mock('echarts', () => ({
  init: vi.fn(() => mockChartInstance)
}))

vi.mock('element-plus', async () => {
  return {
    vLoading: {
      mounted: vi.fn(),
      updated: vi.fn(),
      unmounted: vi.fn()
    }
  }
})

describe('AIDashboard.vue', () => {
  let wrapper: any
  let store: any

  const mockUsageData = {
    totalCalls: 0,
    monthCalls: 0,
    remainingCredits: 0
  }

  const mockPerformanceData = {
    avgResponseTime: 200,
    successRate: 95
  }

  const mockTasksData = {
    total: 1500,
    success: 1400,
    failed: 100
  }

  const mockTrendData = {
    dates: ['2024-01-01', '2024-01-02'],
    values: [100, 200]
  }

  const mockModelUsageData = [
    { model: 'gpt-4', count: 500 },
    { model: 'gpt-3.5', count: 300 }
  ]

  beforeEach(async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    store = useAIStore()
    
    // Mock store methods
    store.fetchUsage = vi.fn().mockResolvedValue(mockUsageData)
    store.fetchPerformance = vi.fn().mockResolvedValue(mockPerformanceData)
    store.fetchTasks = vi.fn().mockResolvedValue(mockTasksData)
    store.fetchTrend = vi.fn().mockResolvedValue(mockTrendData)
    store.fetchModelUsage = vi.fn().mockResolvedValue(mockModelUsageData)

    wrapper = mount(AIDashboard, {
      global: {
        plugins: [pinia],
        directives: {
          loading: vLoading
        },
        stubs: {
          'el-row': {
            template: '<div><slot></slot></div>'
          },
          'el-col': {
            template: '<div><slot></slot></div>'
          },
          'el-card': {
            template: '<div><div class="card-header"><slot name="header"></slot></div><div><slot></slot></div></div>'
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot></slot></button>',
            emits: ['click']
          },
          'el-statistic': {
            template: '<div class="el-statistic"><div class="el-statistic__content">{{ value }}</div></div>',
            props: ['value']
          },
          'el-select': {
            template: '<select v-model="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue'],
            emits: ['change', 'update:modelValue']
          },
          'el-option': {
            template: '<option :value="value"><slot></slot></option>',
            props: ['value']
          },
          'el-progress': {
            template: '<div class="el-progress"></div>'
          }
        }
      }
    })

    // 等待初始数据加载完成
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
  })

  afterEach(() => {
    wrapper.unmount()
    vi.clearAllMocks()
  })

  it('应该在挂载时获取所有数据', async () => {
    expect(store.fetchUsage).toHaveBeenCalled()
    expect(store.fetchPerformance).toHaveBeenCalled()
    expect(store.fetchTasks).toHaveBeenCalled()
    expect(store.fetchTrend).toHaveBeenCalled()
    expect(store.fetchModelUsage).toHaveBeenCalled()
  })

  it('应该正确显示使用统计', async () => {
    await wrapper.vm.refreshUsage()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    const totalCalls = wrapper.find('[data-test="total-calls"] .el-statistic__content')
    const monthCalls = wrapper.find('[data-test="month-calls"] .el-statistic__content')
    const remainingCredits = wrapper.find('[data-test="remaining-credits"] .el-statistic__content')
    
    expect(totalCalls.text()).toBe('0')
    expect(monthCalls.text()).toBe('0')
    expect(remainingCredits.text()).toBe('0')
  })

  it('应该正确显示性能统计', async () => {
    await wrapper.vm.refreshPerformance()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    const avgResponseTime = wrapper.find('[data-test="avg-response-time"] .el-statistic__content')
    const successRate = wrapper.find('[data-test="success-rate"] .el-statistic__content')
    
    expect(avgResponseTime.text()).toBe('200')
    expect(successRate.text()).toBe('95')
  })

  it('应该正确显示任务统计', async () => {
    await wrapper.vm.refreshTasks()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    const totalTasks = wrapper.find('[data-test="total-tasks"] .el-statistic__content')
    const successTasks = wrapper.find('[data-test="success-tasks"] .el-statistic__content')
    const failedTasks = wrapper.find('[data-test="failed-tasks"] .el-statistic__content')
    
    expect(totalTasks.text()).toBe('1500')
    expect(successTasks.text()).toBe('1400')
    expect(failedTasks.text()).toBe('100')
  })

  it('应该能切换时间范围', async () => {
    const select = wrapper.find('select')
    await wrapper.vm.$emit('update:modelValue', '7d')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    expect(store.fetchTrend).toHaveBeenCalledWith('7d')
  })

  it('应该正确初始化图表', async () => {
    expect(echarts.init).toHaveBeenCalledTimes(2)
  })

  it('应该在窗口大小改变时调整图表大小', async () => {
    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    expect(mockChartInstance.resize).toHaveBeenCalled()
  })

  it('应该正确处理加载状态', async () => {
    wrapper.vm.loading.usage = true
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    const loading = wrapper.find('[data-test="usage-loading"]')
    expect(loading.exists()).toBe(true)
  })

  it('应该能刷新数据', async () => {
    const refreshButton = wrapper.find('[data-test="refresh-button"]')
    await refreshButton.trigger('click')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    expect(store.fetchUsage).toHaveBeenCalled()
  })

  it('应该在卸载时清理图表实例', async () => {
    wrapper.vm.trendInstance = mockChartInstance
    wrapper.vm.modelInstance = mockChartInstance
    
    wrapper.unmount()
    
    expect(mockChartInstance.dispose).toHaveBeenCalledTimes(2)
  })

  it('应该正确处理数据加载失败', async () => {
    store.fetchUsage.mockRejectedValueOnce(new Error('API Error'))
    
    await wrapper.vm.refreshUsage()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    expect(wrapper.vm.usage.totalCalls).toBe(0)
    expect(wrapper.vm.usage.monthCalls).toBe(0)
    expect(wrapper.vm.usage.remainingCredits).toBe(0)
  })

  it('应该正确更新图表数据', async () => {
    const mockSetOption = vi.fn()
    const mockInstance = {
      ...mockChartInstance,
      setOption: mockSetOption
    }
    
    wrapper.vm.trendInstance = mockInstance
    wrapper.vm.modelInstance = mockInstance
    
    await wrapper.vm.refreshTrend()
    await wrapper.vm.refreshModels()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))
    
    expect(mockSetOption).toHaveBeenCalledTimes(2)
  })
}) 