import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessageBox } from 'element-plus'
import Monitor from '@/views/monitor/Monitor.vue'
import { useMonitorStore } from '@/stores/monitor'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { nextTick } from 'vue'
import { ElMessage } from 'element-plus'

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

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

describe('Monitor.vue', () => {
  let wrapper: any
  let store: any

  const mockMetrics = {
    timestamp: new Date().toISOString(),
    cpu: {
      usage: 50,
      cores: 4,
      temperature: 45
    },
    memory: {
      total: 16 * 1024 * 1024 * 1024, // 16GB in bytes
      used: 8 * 1024 * 1024 * 1024,   // 8GB in bytes
      usagePercentage: 50
    },
    disk: {
      total: '500 GB',
      used: '250 GB',
      usagePercentage: 50
    },
    network: {
      upload: '10 MB/s',
      download: '20 MB/s',
      latency: 5
    }
  }

  const mockLogs = [
    {
      id: 1,
      timestamp: new Date().toISOString(),
      level: 'INFO',
      message: '系统启动成功'
    },
    {
      id: 2,
      timestamp: new Date().toISOString(),
      level: 'WARNING',
      message: '内存使用率超过50%'
    }
  ]

  const mockProcesses = [
    {
      pid: 1,
      name: 'nginx',
      cpu: 1.5,
      memory: 256 * 1024 * 1024, // 256MB in bytes
      status: 'RUNNING'
    },
    {
      pid: 2,
      name: 'mysql',
      cpu: 2.0,
      memory: 512 * 1024 * 1024, // 512MB in bytes
      status: 'RUNNING'
    }
  ]

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          metrics: mockMetrics,
          logs: mockLogs,
          processList: mockProcesses,
          error: null,
          loading: false,
          isMonitoring: false
        }
      }
    })

    store = useMonitorStore()

    // Mock store methods
    store.fetchSystemMetrics.mockResolvedValue({ data: mockMetrics })
    store.fetchSystemLogs.mockResolvedValue({ data: mockLogs })
    store.fetchProcessList.mockResolvedValue({ data: mockProcesses })
    store.killProcess.mockResolvedValue(undefined)
    store.startMonitoring.mockImplementation(() => {})
    store.stopMonitoring.mockImplementation(() => {})

    wrapper = mount(Monitor, {
      global: {
        plugins: [pinia],
        components: {
          'el-icon': {
            template: '<span><slot/></span>'
          }
        },
        stubs: {
          'el-card': {
            template: '<div class="monitor-card"><div class="el-card__header" v-if="$slots.header"><slot name="header"/></div><div class="el-card__body"><slot/></div></div>'
          },
          'el-button': {
            template: '<button type="button" :class="[`el-button--${$attrs.type || \'default\'}`]" v-bind="$attrs" @click="$emit(\'click\')"><slot/></button>',
            inheritAttrs: false
          },
          'el-input': {
            template: '<div class="el-input"><input type="text" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" v-bind="$attrs"/></div>',
            props: ['modelValue']
          },
          'el-tag': {
            template: '<span class="el-tag" :class="[`el-tag--${type || \'info\'}`]"><slot/></span>',
            props: ['type']
          },
          'el-table': {
            template: '<div class="el-table"><table><tbody><tr v-for="(row, index) in data" :key="index"><td v-for="col in $slots.default" :key="col.props?.prop"><slot v-if="col.props?.prop" :name="col.props.prop" :row="row" :$index="index">{{ row[col.props.prop] }}</slot></td></tr></tbody></table></div>',
            props: ['data']
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot v-if="$slots.default" :row="row" :$index="$index"/><template v-else>{{ row && row[prop] }}</template></div>',
            props: ['prop', 'label', 'width'],
            data() {
              return {
                row: null,
                $index: 0
              }
            }
          },
          'el-alert': {
            template: '<div class="el-alert" :class="[`el-alert--${type}`]" role="alert" v-if="title"><div class="el-alert__content"><span class="el-alert__title">{{ title }}</span><slot/></div></div>',
            props: ['title', 'type']
          },
          'el-dialog': true,
          'el-progress': true
        }
      }
    })

    await nextTick()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('应该正确渲染监控容器', () => {
      expect(wrapper.find('[data-test="monitor-container"]').exists()).toBe(true)
    })

    it('应该正确渲染系统指标卡片', () => {
      const cards = wrapper.findAll('.monitor-card')
      expect(cards.length).toBe(4) // CPU、内存、磁盘、网络

      // 验证CPU卡片
      const cpuCard = wrapper.find('[data-test="cpu-card"]')
      expect(cpuCard.exists()).toBe(true)
      expect(wrapper.find('[data-test="cpu-usage"]').exists()).toBe(true)
      expect(wrapper.find('[data-test="cpu-cores"]').exists()).toBe(true)

      // 验证内存卡片
      const memoryCard = wrapper.find('[data-test="memory-card"]')
      expect(memoryCard.exists()).toBe(true)
      expect(wrapper.find('[data-test="memory-usage"]').exists()).toBe(true)
    })

    it('应该正确渲染日志表格', () => {
      const logsTable = wrapper.find('[data-test="logs-table"]')
      expect(logsTable.exists()).toBe(true)

      // 验证日志级别标签
      const logLevels = wrapper.findAll('[data-test^="log-level-"]')
      expect(logLevels).toHaveLength(mockLogs.length)
    })

    it('应该正确渲染进程列表', () => {
      const processTable = wrapper.find('[data-test="process-table"]')
      expect(processTable.exists()).toBe(true)

      // 验证进程状态标签
      const processStatuses = wrapper.findAll('[data-test^="process-status-"]')
      expect(processStatuses).toHaveLength(mockProcesses.length)
    })
  })

  describe('交互功能', () => {
    it('应该支持进程搜索', async () => {
      const searchInput = wrapper.find('[data-test="process-search"] input')
      expect(searchInput.exists()).toBe(true)
      
      await searchInput.setValue('nginx')
      await nextTick()
      
      const processTable = wrapper.find('[data-test="process-table"]')
      expect(processTable.exists()).toBe(true)
    })

    it('应该能终止进程', async () => {
      const killButton = wrapper.find('[data-test="kill-process-1"]')
      expect(killButton.exists()).toBe(true)
      
      await killButton.trigger('click')
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(store.killProcess).toHaveBeenCalledWith(1)
      expect(store.fetchProcessList).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该显示错误提示', async () => {
      await store.$patch({ error: '获取系统指标失败' })
      await nextTick()
      
      const errorAlert = wrapper.find('[data-test="error-alert"]')
      expect(errorAlert.exists()).toBe(true)
    })

    it('应该处理进程终止失败', async () => {
      store.killProcess.mockRejectedValueOnce(new Error('终止失败'))
      
      const killButton = wrapper.find('[data-test="kill-process-1"]')
      expect(killButton.exists()).toBe(true)
      
      await killButton.trigger('click')
      
      expect(ElMessage.error).toHaveBeenCalledWith('终止进程失败：终止失败')
    })
  })
})