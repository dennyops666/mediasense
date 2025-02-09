import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import AlertList from '@/components/monitor/AlertList.vue'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'
import type { Alert } from '@/types/monitor'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('AlertList.vue', () => {
  const mockAlerts: Alert[] = [
    {
      id: '1',
      message: 'CPU使用率过高',
      level: 'critical',
      timestamp: '2024-03-20T10:00:00Z',
      source: 'system'
    },
    {
      id: '2',
      message: '内存使用率过高',
      level: 'warning',
      timestamp: '2024-03-20T10:01:00Z',
      source: 'system'
    }
  ]

  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          alerts: mockAlerts,
          loading: false
        }
      }
    })

    wrapper = mount(AlertList, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-button': true,
          'el-pagination': true
        }
      }
    })

    store = useMonitorStore()
  })

  describe('告警列表渲染', () => {
    it('应该正确渲染告警列表', () => {
      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(mockAlerts.length)
    })

    it('应该显示告警级别标签', () => {
      const levelTags = wrapper.findAll('[data-test="alert-level"]')
      expect(levelTags[0].text()).toBe('严重')
      expect(levelTags[1].text()).toBe('警告')
    })

    it('应该显示告警时间', () => {
      const timestamps = wrapper.findAll('[data-test="alert-time"]')
      expect(timestamps[0].text()).toContain('2024-03-20 10:00:00')
    })

    it('应该显示告警消息', () => {
      const messages = wrapper.findAll('[data-test="alert-message"]')
      expect(messages[0].text()).toBe('CPU使用率过高')
    })
  })

  describe('告警操作', () => {
    it('应该能确认告警', async () => {
      const ackButton = wrapper.find('[data-test="ack-alert-1"]')
      await ackButton.trigger('click')

      expect(store.handleAcknowledgeAlert).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('已确认告警')
    })

    it('应该能清空所有告警', async () => {
      const clearButton = wrapper.find('[data-test="clear-all"]')
      await clearButton.trigger('click')

      expect(store.clearAllAlerts).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('已清空所有告警')
    })
  })

  describe('告警过滤', () => {
    it('应该能按级别过滤告警', async () => {
      const levelFilter = wrapper.find('[data-test="level-filter"]')
      await levelFilter.setValue('critical')
      await levelFilter.trigger('change')

      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(1)
    })

    it('应该能按时间范围过滤告警', async () => {
      const datePicker = wrapper.find('[data-test="date-range"]')
      await datePicker.vm.$emit('change', ['2024-03-20', '2024-03-21'])

      expect(store.fetchAlerts).toHaveBeenCalledWith({
        startTime: '2024-03-20',
        endTime: '2024-03-21'
      })
    })
  })

  describe('加载状态', () => {
    it('应该显示加载状态', async () => {
      await wrapper.setData({ loading: true })
      
      const loading = wrapper.find('[data-test="loading"]')
      expect(loading.exists()).toBe(true)
    })

    it('加载失败时应该显示错误信息', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })
  })

  describe('分页功能', () => {
    it('应该能切换页码', async () => {
      const pagination = wrapper.find('.el-pagination')
      await pagination.vm.$emit('current-change', 2)

      expect(store.fetchAlerts).toHaveBeenCalledWith({
        page: 2,
        pageSize: 10
      })
    })

    it('应该能改变每页显示数量', async () => {
      const pagination = wrapper.find('.el-pagination')
      await pagination.vm.$emit('size-change', 20)

      expect(store.fetchAlerts).toHaveBeenCalledWith({
        page: 1,
        pageSize: 20
      })
    })
  })
}) 