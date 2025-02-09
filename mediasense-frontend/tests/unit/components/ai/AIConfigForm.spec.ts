import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import AIConfigForm from '@/components/ai/AIConfigForm.vue'
import { useAIStore } from '@/stores/ai'
import { nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { createTestingPinia } from '@pinia/testing'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

const mockConfig = {
  apiKey: 'test-api-key',
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  topP: 0.9,
  frequencyPenalty: 0.5,
  presencePenalty: 0.5,
  stopSequences: ['END'],
  systemPrompt: '你是一个新闻助手'
}

describe('AIConfigForm.vue', () => {
  let wrapper: any
  let store: any

  beforeEach(async () => {
    // 创建一个新的 pinia 实例
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        ai: {
          config: mockConfig,
          loading: false,
          error: null
        }
      }
    })

    // 获取 store 实例
    store = useAIStore(pinia)

    // 模拟 store 方法
    store.updateConfig.mockResolvedValue(mockConfig)
    store.testConnection.mockResolvedValue(true)

    wrapper = mount(AIConfigForm, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-form': {
            template: '<form><slot></slot></form>',
            methods: {
              validate: vi.fn().mockResolvedValue(true),
              resetFields: vi.fn()
            }
          },
          'el-form-item': {
            template: '<div class="el-form-item"><slot></slot></div>'
          },
          'el-input': {
            template: '<input v-model="value" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', value)
                }
              }
            }
          },
          'el-input-number': {
            template: '<input type="number" v-model.number="value" @input="$emit(\'update:modelValue\', Number($event.target.value))" />',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', Number(value))
                }
              }
            }
          },
          'el-select': {
            template: '<select v-model="value" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', value)
                }
              }
            }
          },
          'el-option': {
            template: '<option :value="value"><slot></slot></option>',
            props: ['value']
          },
          'el-slider': {
            template: '<input type="range" v-model.number="value" @input="$emit(\'update:modelValue\', Number($event.target.value))" />',
            props: ['modelValue'],
            computed: {
              value: {
                get() {
                  return this.modelValue
                },
                set(value) {
                  this.$emit('update:modelValue', Number(value))
                }
              }
            }
          },
          'el-button': {
            template: '<button :disabled="loading" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['loading']
          }
        }
      }
    })

    await nextTick()
  })

  it('应该正确渲染表单字段', () => {
    const form = wrapper.find('form')
    expect(form.exists()).toBe(true)

    const apiKeyInput = wrapper.find('input[type="text"]')
    const modelSelect = wrapper.find('select')
    const maxTokensInput = wrapper.find('input[type="number"]')
    const temperatureSlider = wrapper.find('input[type="range"]')

    expect(apiKeyInput.exists()).toBe(true)
    expect(modelSelect.exists()).toBe(true)
    expect(maxTokensInput.exists()).toBe(true)
    expect(temperatureSlider.exists()).toBe(true)
  })

  it('应该有正确的默认值', () => {
    const apiKeyInput = wrapper.find('input[type="text"]')
    const modelSelect = wrapper.find('select')
    const maxTokensInput = wrapper.find('input[type="number"]')
    const temperatureSlider = wrapper.find('input[type="range"]')

    expect(apiKeyInput.element.value).toBe(mockConfig.apiKey)
    expect(modelSelect.element.value).toBe(mockConfig.model)
    expect(Number(maxTokensInput.element.value)).toBe(mockConfig.maxTokens)
    expect(Number(temperatureSlider.element.value)).toBe(mockConfig.temperature)
  })

  it('应该能重置表单', async () => {
    const resetButton = wrapper.findAll('button').find(btn => btn.text().includes('重置'))
    expect(resetButton.exists()).toBe(true)
    
    // 修改表单值
    const apiKeyInput = wrapper.find('input[type="text"]')
    await apiKeyInput.setValue('new-api-key')
    
    await resetButton.trigger('click')
    await nextTick()
    
    expect(apiKeyInput.element.value).toBe(mockConfig.apiKey)
  })

  it('应该在提交成功时发出事件', async () => {
    const submitButton = wrapper.findAll('button').find(btn => btn.text().includes('保存'))
    expect(submitButton.exists()).toBe(true)
    
    await submitButton.trigger('click')
    await nextTick()
    
    expect(store.updateConfig).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('配置已保存')
  })

  it('应该能测试API连接', async () => {
    const testButton = wrapper.findAll('button').find(btn => btn.text().includes('测试连接'))
    expect(testButton.exists()).toBe(true)

    await testButton.trigger('click')
    await nextTick()
    
    expect(store.testConnection).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('连接成功')

    // 测试失败状态
    store.testConnection.mockRejectedValueOnce(new Error('连接失败'))
    await testButton.trigger('click')
    await nextTick()
    
    expect(ElMessage.error).toHaveBeenCalledWith('连接失败')
  })

  it('应该正确处理加载状态', async () => {
    store.$patch({ loading: true })
    await nextTick()

    const buttons = wrapper.findAll('button')
    buttons.forEach(button => {
      expect(button.attributes('disabled')).toBe('true')
    })

    store.$patch({ loading: false })
    await nextTick()

    buttons.forEach(button => {
      expect(button.attributes('disabled')).toBeFalsy()
    })
  })
})
