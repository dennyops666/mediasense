<template>
  <div class="crawler-config-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
      data-test="crawler-config-form"
    >
      <el-form-item label="名称" prop="name" data-test="crawler-name">
        <el-input v-model="formData.name" placeholder="请输入爬虫名称" />
      </el-form-item>

      <el-form-item label="类型" prop="type" data-test="crawler-type">
        <el-select v-model="formData.type" placeholder="请选择爬虫类型">
          <el-option label="新闻" value="news" />
          <el-option label="博客" value="blog" />
          <el-option label="社交媒体" value="social" />
        </el-select>
      </el-form-item>

      <el-form-item label="URL" prop="url" data-test="crawler-url">
        <el-input v-model="formData.url" placeholder="请输入目标URL" />
      </el-form-item>

      <el-form-item label="请求方法" prop="method" data-test="crawler-method">
        <el-select v-model="formData.method" placeholder="请选择请求方法">
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
        </el-select>
      </el-form-item>

      <el-form-item label="选择器" prop="selectors">
        <div v-for="(selector, index) in formData.selectors" :key="index" class="selector-item" data-test="selector-item">
          <el-input v-model="selector.field" placeholder="字段名" />
          <el-input v-model="selector.selector" placeholder="选择器" />
          <el-select v-model="selector.type">
            <el-option label="CSS" value="css" />
            <el-option label="XPath" value="xpath" />
          </el-select>
          <el-button type="danger" @click="removeSelector(index)" data-test="delete-selector">删除</el-button>
        </div>
        <el-button type="primary" @click="addSelector" data-test="add-selector">添加选择器</el-button>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit" data-test="submit-button">
          {{ mode === 'create' ? '创建' : '更新' }}
        </el-button>
        <el-button @click="handleReset" data-test="reset-button">重置</el-button>
        <el-button type="success" @click="handleTest" data-test="test-button">测试</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { FormInstance } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerConfig } from '@/types/crawler'

const props = defineProps<{
  initialConfig?: Partial<CrawlerConfig>
  mode: 'create' | 'edit'
}>()

const store = useCrawlerStore()
const formRef = ref<FormInstance>()

const formData = reactive<Partial<CrawlerConfig>>({
  name: '',
  type: 'news',
  url: '',
  method: 'GET',
  headers: [],
  selectors: [],
  timeout: 30,
  retries: 3,
  concurrency: 1,
  enabled: true
})

const rules = {
  name: [
    { required: true, message: '请输入爬虫名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择爬虫类型', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入目标URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ]
}

onMounted(() => {
  if (props.initialConfig) {
    Object.assign(formData, props.initialConfig)
  }
})

const addSelector = () => {
  formData.selectors?.push({
    field: '',
    selector: '',
    type: 'css'
  })
}

const removeSelector = (index: number) => {
  formData.selectors?.splice(index, 1)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    if (props.mode === 'create') {
      await store.createConfig(formData)
      ElMessage.success('创建爬虫配置成功')
    } else {
      await store.updateConfig(props.initialConfig?.id!, formData)
      ElMessage.success('更新配置成功')
    }
  } catch (error) {
    ElMessage.error('表单验证失败')
  }
}

const handleReset = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const handleTest = async () => {
  try {
    await store.testConfig(formData)
    ElMessage.success('测试成功')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}
</script>

<style scoped>
.crawler-config-form {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.selector-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
</style> 