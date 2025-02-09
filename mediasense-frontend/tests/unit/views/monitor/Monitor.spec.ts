import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessageBox, ElMessage } from 'element-plus'
import Monitor from '@/views/monitor/Monitor.vue'
import { useMonitorStore } from '@/stores/monitor'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { nextTick, defineComponent } from 'vue'
import { flushPromises } from '@vue/test-utils'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue(true)
  }
}))

const vLoading = {
  mounted(el: HTMLElement, binding: any) {
    el.setAttribute('loading', binding.value ? 'true' : 'false')
  },
  updated(el: HTMLElement, binding: any) {
    el.setAttribute('loading', binding.value ? 'true' : 'false')
  }
}

describe('Monitor.vue', () => {
  let wrapper: any
  let store: any

  const mockMetrics = {
    cpu: {
      usage: 50,
      cores: 4,
      temperature: 45
    },
    memory: {
      total: '16 GB',
      used: '8 GB',
      usagePercentage: 50
    }
  }

  const mockLogs = [
    {
      id: 1,
      timestamp: '2024-03-20T10:00:00Z',
      level: 'INFO',
      message: '系统启动成功'
    },
    {
      id: 2,
      timestamp: '2024-03-20T10:01:00Z',
      level: 'WARNING',
      message: '内存使用率超过50%'
    }
  ]

  const mockProcesses = [
    {
      pid: 1,
      name: 'nginx',
      status: 'RUNNING',
      cpu: 1.5,
      memory: 256
    },
    {
      pid: 2,
      name: 'mysql',
      status: 'RUNNING',
      cpu: 2.0,
      memory: 512
    }
  ]

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          metrics: mockMetrics,
          logs: mockLogs,
          processes: mockProcesses,
          error: null,
          loading: false,
          isMonitoring: false
        }
      }
    })

    store = useMonitorStore(pinia)

    // Mock store methods
    store.fetchSystemMetrics = vi.fn().mockResolvedValue(mockMetrics)
    store.fetchSystemLogs = vi.fn().mockResolvedValue({ items: mockLogs })
    store.fetchProcessList = vi.fn().mockResolvedValue(mockProcesses)
    store.killProcess = vi.fn().mockResolvedValue(undefined)
    store.startMonitoring = vi.fn()
    store.stopMonitoring = vi.fn()

    wrapper = mount(Monitor, {
      global: {
        plugins: [pinia],
        directives: {
          loading: vLoading
        },
        stubs: {
          'el-card': {
            template: `
              <div class="el-card">
                <div class="el-card__header" v-if="$slots.header">
                  <slot name="header"/>
                </div>
                <div class="el-card__body">
                  <slot/>
                </div>
              </div>
            `
          },
          'el-button': {
            template: `
              <button 
                @click="$emit('click')" 
                :class="['el-button', type ? 'el-button--' + type : '']"
                :data-test="$attrs['data-test']"
              >
                <slot/>
              </button>
            `,
            props: ['type', 'size'],
            inheritAttrs: false
          },
          'el-input': {
            template: `
              <div class="el-input" :data-test="$attrs['data-test']">
                <input 
                  :value="modelValue"
                  @input="$emit('update:modelValue', $event.target.value)"
                  class="el-input__inner"
                />
              </div>
            `,
            props: ['modelValue'],
            emits: ['update:modelValue'],
            inheritAttrs: false
          },
          'el-tag': {
            template: `
              <span 
                :class="['el-tag', type ? 'el-tag--' + type : '']"
                :data-test="$attrs['data-test']"
              >
                <slot/>
              </span>
            `,
            props: ['type'],
            inheritAttrs: false
          },
          'el-table': {
            template: `
              <div class="el-table" :data-test="$attrs['data-test']">
                <table>
                  <thead>
                    <tr>
                      <th v-for="col in $slots.default()" :key="col.props?.prop">
                        {{ col.props?.label }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in data" :key="row.id || row.pid">
                      <td v-for="col in $slots.default()" :key="col.props?.prop">
                        <component 
                          :is="col"
                          v-bind="{ row }"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            `,
            props: ['data'],
            inheritAttrs: false
          },
          'el-table-column': {
            template: `
              <div v-if="$slots.default">
                <slot :row="row"/>
              </div>
              <div v-else>
                {{ row[prop] }}
              </div>
            `,
            props: ['prop', 'label', 'row']
          },
          'el-alert': {
            template: `
              <div 
                v-if="title"
                class="el-alert"
                :class="['el-alert--' + type]"
                :data-test="$attrs['data-test']"
              >
                <div class="el-alert__content">
                  <span class="el-alert__title">{{ title }}</span>
                  <slot/>
                </div>
              </div>
            `,
            props: ['title', 'type'],
            inheritAttrs: false
          }
        }
      }
    })

    await nextTick()
  })

  afterEach(() => {
    wrapper.unmount()
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('应该正确渲染监控容器', () => {
      expect(wrapper.find('[data-test="monitor-container"]').exists()).toBe(true)
    })

    it('应该正确渲染日志表格', () => {
      const logsTable = wrapper.find('[data-test="logs-table"]')
      expect(logsTable.exists()).toBe(true)

      const logEntries = wrapper.findAll('tr').filter(row => 
        row.find('[data-test^="log-level-"]').exists()
      )
      expect(logEntries.length).toBe(mockLogs.length)
    })

    it('应该正确渲染进程列表', () => {
      const processTable = wrapper.find('[data-test="process-table"]')
      expect(processTable.exists()).toBe(true)

      const processEntries = wrapper.findAll('tr').filter(row => 
        row.find('[data-test^="process-status-"]').exists()
      )
      expect(processEntries.length).toBe(mockProcesses.length)
    })
  })

  describe('交互功能', () => {
    it('应该支持进程搜索', async () => {
      const searchInput = wrapper.find('[data-test="process-search"] input')
      expect(searchInput.exists()).toBe(true)
      
      await searchInput.setValue('nginx')
      await nextTick()
      
      const processTable = wrapper.find('[data-test="process-table"]')
      const processRows = processTable.findAll('tr').filter(row => 
        row.find('[data-test^="process-status-"]').exists()
      )
      expect(processRows.length).toBe(1)
      expect(processRows[0].text()).toContain('nginx')
    })

    it('应该能终止进程', async () => {
      const killButton = wrapper.find('[data-test="kill-process-1"]')
      expect(killButton.exists()).toBe(true)
      
      await killButton.trigger('click')
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(store.killProcess).toHaveBeenCalledWith(1)
      expect(store.fetchProcessList).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('进程已终止')
    })
  })

  describe('错误处理', () => {
    it('应该显示错误提示', async () => {
      await store.$patch({ error: '获取系统指标失败' })
      await nextTick()
      
      const errorAlert = wrapper.find('[data-test="error-alert"]')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.text()).toContain('获取系统指标失败')
    })

    it('应该处理进程终止失败', async () => {
      store.killProcess.mockRejectedValueOnce(new Error('终止失败'))
      
      const killButton = wrapper.find('[data-test="kill-process-1"]')
      expect(killButton.exists()).toBe(true)
      
      await killButton.trigger('click')
      await nextTick()
      
      expect(ElMessage.error).toHaveBeenCalledWith('终止进程失败：终止失败')
    })
  })

  describe('系统指标', () => {
    it('应该正确渲染CPU指标', () => {
      const cpuCard = wrapper.find('[data-test="cpu-card"]')
      expect(cpuCard.exists()).toBe(true)
      expect(cpuCard.find('[data-test="cpu-usage"]').text()).toContain('50%')
      expect(cpuCard.find('[data-test="cpu-cores"]').text()).toContain('核心数: 4')
    })

    it('应该正确渲染内存指标', () => {
      const memoryCard = wrapper.find('[data-test="memory-card"]')
      expect(memoryCard.exists()).toBe(true)
      expect(memoryCard.find('[data-test="memory-usage"]').text()).toContain('50%')
      expect(memoryCard.text()).toContain('已用: 8 GB / 16 GB')
    })

    it('应该在加载状态下显示loading', async () => {
      const vm = wrapper.vm as any
      vm.loading = true
      await nextTick()
      const container = wrapper.find('[data-test="monitor-container"]')
      expect(container.attributes('loading')).toBe('true')
    })
  })

  describe('自动刷新', () => {
    it('应该在挂载时启动监控', () => {
      expect(store.startMonitoring).toHaveBeenCalled()
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
      expect(store.fetchSystemLogs).toHaveBeenCalled()
      expect(store.fetchProcessList).toHaveBeenCalled()
    })

    it('应该在卸载时停止监控', () => {
      wrapper.unmount()
      expect(store.stopMonitoring).toHaveBeenCalled()
    })
  })
})