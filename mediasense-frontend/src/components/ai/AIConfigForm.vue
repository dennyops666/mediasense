<template>
  <div class="ai-config-form">
    <el-form 
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
      data-test="ai-config-form"
    >
      <el-form-item label="API Key" prop="apiKey">
        <el-input 
          v-model="formData.apiKey" 
          placeholder="请输入 API Key"
          show-password
          :disabled="loading"
          data-test="api-key-input"
        />
      </el-form-item>

      <el-form-item label="模型" prop="model">
        <el-select 
          v-model="formData.model" 
          placeholder="请选择模型" 
          :disabled="loading"
          data-test="model-select"
        >
          <el-option
            v-for="item in modelOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="最大令牌数" prop="maxTokens">
        <el-input-number 
          v-model="formData.maxTokens"
          :min="1"
          :max="4096"
          :disabled="loading"
          data-test="max-tokens-input"
        />
      </el-form-item>

      <el-form-item label="温度" prop="temperature">
        <el-slider
          v-model="formData.temperature"
          :min="0"
          :max="2"
          :step="0.1"
          :disabled="loading"
          data-test="temperature-slider"
        />
      </el-form-item>

      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleSubmit" 
          :disabled="loading"
          data-test="submit-button"
        >
          保存
        </el-button>
        <el-button 
          @click="handleReset" 
          :disabled="loading"
          data-test="reset-button"
        >
          重置
        </el-button>
        <el-button 
          @click="handleTestConnection" 
          :disabled="loading"
          data-test="test-connection-button"
        >
          测试连接
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAIStore } from '@/stores/ai'

interface FormData {
  apiKey: string
  model: string
  maxTokens: number
  temperature: number
}

const store = useAIStore()
const loading = ref(false)

const emit = defineEmits<{
  (e: 'submit', data: FormData): void
}>()

const formRef = ref<FormInstance>()

const formData = reactive<FormData>({
  apiKey: '',
  model: 'gpt-3.5-turbo',
  maxTokens: 2048,
  temperature: 1
})

onMounted(async () => {
  try {
    loading.value = true
    // 从 store 加载初始配置
    const config = store.config
    if (config) {
      formData.apiKey = config.apiKey || ''
      formData.model = config.model || 'gpt-3.5-turbo'
      formData.maxTokens = config.maxTokens || 2048
      formData.temperature = config.temperature || 1
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
})

const modelOptions = [
  { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
  { label: 'GPT-4', value: 'gpt-4' }
]

const rules = {
  apiKey: [
    { required: true, message: '请输入 API Key', trigger: 'blur' },
    { min: 32, message: 'API Key 长度不正确', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请选择模型', trigger: 'change' }
  ],
  maxTokens: [
    { required: true, message: '请输入最大令牌数', trigger: 'blur' },
    { type: 'number', min: 1, max: 4096, message: '令牌数必须在 1-4096 之间', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请设置温度', trigger: 'change' },
    { type: 'number', min: 0, max: 2, message: '温度必须在 0-2 之间', trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (valid) {
      loading.value = true
      await store.updateConfig({ ...formData })
      emit('submit', { ...formData })
      ElMessage.success('配置已保存')
    }
  } catch (error) {
    console.error('验证失败:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const handleTestConnection = async () => {
  try {
    loading.value = true
    await store.testConnection()
    ElMessage.success('连接成功')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '连接失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-config-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
</style>

