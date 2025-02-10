import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import CrawlerTaskList from '../../../../src/components/crawler/CrawlerTaskList.vue'
import { useCrawlerStore } from '../../../../src/stores/crawler'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import type { CrawlerTask } from '../../../../src/types/crawler'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue('confirm')
  }
}))

describe('CrawlerTaskList.vue', () => {
  let wrapper
  let store

  const mockTasks: CrawlerTask[] = [
    {
      id: '1',
      name: '测试任务1',
      type: 'web',
      status: 'running',
      schedule: '*/5 * * * *',
      config: {},
      lastRunTime: '2024-03-20T10:00:00Z',
      count: 100,
      configId: '1',
      startTime: '2024-03-20T10:00:00Z',
      totalItems: 100,
      successItems: 50,
      failedItems: 0,
      createdAt: '2024-03-20T10:00:00Z',
      updatedAt: '2024-03-20T10:00:00Z'
    },
    {
      id: '2',
      name: '测试任务2',
      type: 'web',
      status: 'stopped',
      schedule: '*/10 * * * *',
      config: {},
      lastRunTime: '2024-03-20T09:00:00Z',
      count: 50,
      configId: '2',
      startTime: '2024-03-20T09:00:00Z',
      endTime: '2024-03-20T09:30:00Z',
      totalItems: 50,
      successItems: 50,
      failedItems: 0,
      createdAt: '2024-03-20T09:00:00Z',
      updatedAt: '2024-03-20T09:30:00Z'
    }
  ]

  beforeEach(() => {
    wrapper = mount(CrawlerTaskList, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              crawler: {
                tasks: mockTasks,
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-table': {
            template: `
              <div class="el-table">
                <slot name="selection" v-for="(row, index) in data" :row="row" :$index="index"></slot>
                <table>
                  <tbody>
                    <tr v-for="(row, index) in data" :key="row.id" class="task-row">
                      <td><slot name="selection" :row="row" :$index="index"></slot></td>
                      <td><slot name="name" :row="row"></slot></td>
                      <td><slot name="type" :row="row"></slot></td>
                      <td><slot name="status" :row="row"></slot></td>
                      <td><slot name="progress" :row="row"></slot></td>
                      <td><slot name="operation" :row="row"></slot></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            `,
            props: ['data']
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot></slot></div>'
          },
          'el-button': {
            template: `
              <button 
                :class="['el-button', type ? 'el-button--' + type : '']"
                :disabled="disabled"
                :data-test="dataTest"
                @click="$emit('click')"
              >
                <slot></slot>
              </button>
            `,
            props: ['type', 'disabled', 'dataTest']
          },
          'el-input': {
            template: `
              <input 
                class="el-input"
                :value="modelValue"
                @input="$emit('update:modelValue', $event.target.value)"
                data-test="search-input"
              />
            `,
            props: ['modelValue']
          },
          'el-select': {
            template: `
              <select 
                class="el-select"
                :value="modelValue"
                @change="$emit('update:modelValue', $event.target.value)"
                data-test="status-select"
              >
                <slot></slot>
              </select>
            `,
            props: ['modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['value', 'label']
          },
          'el-tag': {
            template: '<span class="el-tag" :class="type"><slot></slot></span>',
            props: ['type']
          },
          'el-progress': {
            template: '<div class="el-progress"><div :style="{ width: percentage + '%' }"></div></div>',
            props: ['percentage']
          }
        }
      }
    })

    store = useCrawlerStore()
  })

  it('应该正确渲染任务列表', async () => {
    await nextTick()
    const taskRows = wrapper.findAll('.task-row')
    expect(taskRows).toHaveLength(2)
    expect(wrapper.text()).toContain('测试任务1')
    expect(wrapper.text()).toContain('测试任务2')
  })

  it('应该能搜索任务', async () => {
    const searchInput = wrapper.find('[data-test="search-input"]')
    await searchInput.setValue('测试任务1')
    await nextTick()
    expect(store.fetchTasks).toHaveBeenCalledWith(expect.objectContaining({
      keyword: '测试任务1'
    }))
  })

  it('应该能过滤任务状态', async () => {
    const statusSelect = wrapper.find('[data-test="status-select"]')
    await statusSelect.setValue('running')
    await nextTick()
    expect(store.fetchTasks).toHaveBeenCalledWith(expect.objectContaining({
      status: 'running'
    }))
  })

  it('应该能启动任务', async () => {
    const startButton = wrapper.find('[data-test="start-task"]')
    await startButton.trigger('click')
    expect(store.startTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('任务启动成功')
  })

  it('应该能停止任务', async () => {
    const stopButton = wrapper.find('[data-test="stop-task"]')
    await stopButton.trigger('click')
    expect(store.stopTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('任务停止成功')
  })

  it('应该能删除任务', async () => {
    const deleteButton = wrapper.find('[data-test="delete-task"]')
    await deleteButton.trigger('click')
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(store.deleteTask).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
  })

  it('应该处理任务操作失败', async () => {
    store.startTask.mockRejectedValueOnce(new Error('启动失败'))
    const startButton = wrapper.find('[data-test="start-task"]')
    await startButton.trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('启动失败')
  })

  it('应该能批量启动任务', async () => {
    const checkboxes = wrapper.findAll('[data-test="task-checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)
    
    const batchStartButton = wrapper.find('[data-test="batch-start"]')
    await batchStartButton.trigger('click')
    
    expect(store.batchStartTasks).toHaveBeenCalledWith(['1', '2'])
    expect(ElMessage.success).toHaveBeenCalledWith('批量启动成功')
  })

  it('应该能批量停止任务', async () => {
    const checkboxes = wrapper.findAll('[data-test="task-checkbox"]')
    await checkboxes[0].setValue(true)
    await checkboxes[1].setValue(true)
    
    const batchStopButton = wrapper.find('[data-test="batch-stop"]')
    await batchStopButton.trigger('click')
    
    expect(store.batchStopTasks).toHaveBeenCalledWith(['1', '2'])
    expect(ElMessage.success).toHaveBeenCalledWith('批量停止成功')
  })

  it('应该处理错误状态', async () => {
    store.$patch({ error: '获取任务列表失败' })
    await nextTick()
    expect(wrapper.find('[data-test="error-message"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('获取任务列表失败')
  })
})