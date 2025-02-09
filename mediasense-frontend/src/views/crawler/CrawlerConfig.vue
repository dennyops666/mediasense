<template>
  <div class="crawler-config">
    <!-- 配置表单 -->
    <el-form
      ref="formRef"
      :model="configForm"
      :rules="rules"
      label-width="120px"
      class="config-form"
    >
      <!-- 基本配置 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>基本配置</span>
          </div>
        </template>
        
        <el-form-item label="爬虫类型" prop="type">
          <el-select v-model="configForm.type" placeholder="请选择爬虫类型">
            <el-option
              v-for="type in crawlerTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="目标URL" prop="targetUrl">
          <el-input
            v-model="configForm.targetUrl"
            placeholder="请输入目标URL"
            type="textarea"
            :rows="3"
          />
          <div class="form-tip">支持多个URL，每行一个</div>
        </el-form-item>

        <el-form-item label="请求方法" prop="method">
          <el-radio-group v-model="configForm.method">
            <el-radio label="GET">GET</el-radio>
            <el-radio label="POST">POST</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="configForm.method === 'POST'" label="请求体" prop="body">
          <el-input
            v-model="configForm.body"
            type="textarea"
            :rows="5"
            placeholder="请输入JSON格式的请求体"
          />
        </el-form-item>
      </el-card>

      <!-- 请求头配置 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>请求头配置</span>
            <el-button type="primary" link @click="addHeader">
              添加请求头
            </el-button>
          </div>
        </template>

        <div
          v-for="(header, index) in configForm.headers"
          :key="index"
          class="header-item"
        >
          <el-input v-model="header.key" placeholder="Header Key" />
          <el-input v-model="header.value" placeholder="Header Value" />
          <el-button type="danger" link @click="removeHeader(index)">
            删除
          </el-button>
        </div>
      </el-card>

      <!-- 选择器配置 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>选择器配置</span>
            <el-button type="primary" link @click="addSelector">
              添加选择器
            </el-button>
          </div>
        </template>

        <div
          v-for="(selector, index) in configForm.selectors"
          :key="index"
          class="selector-item"
        >
          <el-form-item
            :label="'字段名称'"
            :prop="'selectors.' + index + '.field'"
            :rules="{ required: true, message: '请输入字段名称', trigger: 'blur' }"
          >
            <el-input v-model="selector.field" placeholder="请输入字段名称" />
          </el-form-item>

          <el-form-item
            :label="'选择器'"
            :prop="'selectors.' + index + '.selector'"
            :rules="{ required: true, message: '请输入选择器', trigger: 'blur' }"
          >
            <el-input v-model="selector.selector" placeholder="请输入CSS选择器">
              <template #append>
                <el-select v-model="selector.type" style="width: 100px">
                  <el-option label="CSS" value="css" />
                  <el-option label="XPath" value="xpath" />
                </el-select>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="提取属性">
            <el-input v-model="selector.attr" placeholder="默认提取文本内容" />
          </el-form-item>

          <el-button type="danger" link @click="removeSelector(index)">
            删除选择器
          </el-button>

          <el-divider v-if="index < configForm.selectors.length - 1" />
        </div>
      </el-card>

      <!-- 高级配置 -->
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>高级配置</span>
          </div>
        </template>

        <el-form-item label="请求超时" prop="timeout">
          <el-input-number
            v-model="configForm.timeout"
            :min="1"
            :max="60"
            :step="1"
          />
          <span class="unit-text">秒</span>
        </el-form-item>

        <el-form-item label="重试次数" prop="retries">
          <el-input-number
            v-model="configForm.retries"
            :min="0"
            :max="5"
            :step="1"
          />
        </el-form-item>

        <el-form-item label="并发数" prop="concurrency">
          <el-input-number
            v-model="configForm.concurrency"
            :min="1"
            :max="10"
            :step="1"
          />
        </el-form-item>

        <el-form-item label="代理设置" prop="proxy">
          <el-input v-model="configForm.proxy" placeholder="http://proxy.example.com:8080" />
        </el-form-item>

        <el-form-item label="User-Agent">
          <el-select v-model="configForm.userAgent" placeholder="请选择User-Agent">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Firefox" value="firefox" />
            <el-option label="Safari" value="safari" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-input
            v-if="configForm.userAgent === 'custom'"
            v-model="configForm.customUserAgent"
            placeholder="请输入自定义User-Agent"
            style="margin-top: 10px"
          />
        </el-form-item>
      </el-card>

      <!-- 保存按钮 -->
      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存配置
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'

const store = useCrawlerStore()
const formRef = ref<FormInstance>()
const saving = ref(false)

// 爬虫类型选项
const crawlerTypes = [
  { label: '新闻网站', value: 'news' },
  { label: '社交媒体', value: 'social' },
  { label: '电商网站', value: 'ecommerce' },
  { label: '通用网站', value: 'general' }
]

// 表单数据
const configForm = reactive({
  type: '',
  targetUrl: '',
  method: 'GET',
  body: '',
  headers: [] as { key: string; value: string }[],
  selectors: [] as {
    field: string
    selector: string
    type: 'css' | 'xpath'
    attr: string
  }[],
  timeout: 30,
  retries: 3,
  concurrency: 1,
  proxy: '',
  userAgent: 'chrome',
  customUserAgent: ''
})

// 表单验证规则
const rules = {
  type: [
    { required: true, message: '请选择爬虫类型', trigger: 'change' }
  ],
  targetUrl: [
    { required: true, message: '请输入目标URL', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  body: [
    { 
      validator: (rule: any, value: string, callback: Function) => {
        if (configForm.method === 'POST' && !value) {
          callback(new Error('POST请求必须填写请求体'))
        } else if (value) {
          try {
            JSON.parse(value)
            callback()
          } catch (error) {
            callback(new Error('请输入有效的JSON格式'))
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  timeout: [
    { required: true, message: '请设置请求超时时间', trigger: 'blur' }
  ],
  retries: [
    { required: true, message: '请设置重试次数', trigger: 'blur' }
  ],
  concurrency: [
    { required: true, message: '请设置并发数', trigger: 'blur' }
  ]
}

// 请求头操作
const addHeader = () => {
  configForm.headers.push({ key: '', value: '' })
}

const removeHeader = (index: number) => {
  configForm.headers.splice(index, 1)
}

// 选择器操作
const addSelector = () => {
  configForm.selectors.push({
    field: '',
    selector: '',
    type: 'css',
    attr: ''
  })
}

const removeSelector = (index: number) => {
  configForm.selectors.splice(index, 1)
}

// 表单操作
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    const config = {
      ...configForm,
      userAgent: configForm.userAgent === 'custom' 
        ? configForm.customUserAgent 
        : configForm.userAgent
    }
    
    await store.saveConfig(config)
    ElMessage.success('配置保存成功')
    // TODO: 返回列表页
  } catch (error) {
    if (error instanceof Error) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  // TODO: 返回列表页
}
</script>

<style scoped>
.crawler-config {
  padding: 20px;
}

.config-form {
  max-width: 800px;
  margin: 0 auto;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.header-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.selector-item {
  padding: 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  margin-bottom: 20px;
}

.unit-text {
  margin-left: 10px;
  color: var(--el-text-color-secondary);
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 30px;
}
</style> 