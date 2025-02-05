<template>
  <div class="crawler-list">
    <div class="page-header">
      <h2 class="page-title">爬虫配置管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><plus /></el-icon>
        新建配置
      </el-button>
    </div>

    <el-table
      v-loading="crawlerStore.loading"
      :data="crawlerStore.configs"
      style="width: 100%"
    >
      <el-table-column prop="name" label="配置名称" min-width="150" />
      
      <el-table-column prop="siteName" label="网站名称" min-width="150" />
      
      <el-table-column prop="siteUrl" label="网站地址" min-width="200">
        <template #default="{ row }">
          <el-link type="primary" :href="row.siteUrl" target="_blank">
            {{ row.siteUrl }}
          </el-link>
        </template>
      </el-table-column>
      
      <el-table-column prop="frequency" label="抓取频率" width="120">
        <template #default="{ row }">
          {{ formatFrequency(row.frequency) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="enabled" label="启用状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            :loading="crawlerStore.loading"
            @change="(val: boolean) => handleToggle(row.id, val)"
          />
        </template>
      </el-table-column>
      
      <el-table-column prop="lastRunTime" label="上次运行" width="180">
        <template #default="{ row }">
          {{ row.lastRunTime ? formatDate(row.lastRunTime) : '从未运行' }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button
              type="primary"
              :icon="VideoPlay"
              @click="handleRun(row.id)"
              :disabled="!row.enabled"
            >
              立即运行
            </el-button>
            
            <el-button
              type="primary"
              :icon="Edit"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            
            <el-button
              type="danger"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentConfig ? '编辑配置' : '新建配置'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        
        <el-form-item label="网站名称" prop="siteName">
          <el-input v-model="form.siteName" />
        </el-form-item>
        
        <el-form-item label="网站地址" prop="siteUrl">
          <el-input v-model="form.siteUrl" />
        </el-form-item>
        
        <el-form-item label="抓取频率" prop="frequency">
          <el-input-number
            v-model="form.frequency"
            :min="1"
            :max="10080"
            style="width: 100%"
            placeholder="请输入抓取频率（分钟）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="crawlerStore.loading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import {
  Plus,
  VideoPlay,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import { formatDate } from '@/utils/date'
import type { CrawlerConfig } from '@/types/api'

const crawlerStore = useCrawlerStore()
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const currentConfig = ref<CrawlerConfig | null>(null)

interface CrawlerForm {
  name: string
  siteName: string
  siteUrl: string
  frequency: number
}

const form = reactive<CrawlerForm>({
  name: '',
  siteName: '',
  siteUrl: '',
  frequency: 1440 // 默认每天运行一次（24小时 * 60分钟）
})

const rules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  siteName: [
    { required: true, message: '请输入网站名称', trigger: 'blur' }
  ],
  siteUrl: [
    { required: true, message: '请输入网站地址', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ],
  frequency: [
    { required: true, message: '请输入抓取频率', trigger: 'blur' },
    { type: 'number', min: 1, max: 10080, message: '频率必须在1-10080分钟之间', trigger: 'blur' }
  ]
}

const formatFrequency = (minutes: number) => {
  if (minutes < 60) {
    return `${minutes}分钟`
  } else if (minutes < 1440) {
    return `${minutes / 60}小时`
  } else {
    return `${minutes / 1440}天`
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    siteName: '',
    siteUrl: '',
    frequency: 1440
  })
  currentConfig.value = null
  formRef.value?.resetFields()
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: CrawlerConfig) => {
  currentConfig.value = row
  Object.assign(form, {
    name: row.name,
    siteName: row.siteName,
    siteUrl: row.siteUrl,
    frequency: row.frequency
  })
  dialogVisible.value = true
}

const handleDelete = (row: CrawlerConfig) => {
  ElMessageBox.confirm(
    '确定要删除该爬虫配置吗？删除后无法恢复。',
    '删除确认',
    {
      type: 'warning'
    }
  ).then(async () => {
    await crawlerStore.deleteConfig(row.id)
  })
}

const handleToggle = async (id: string, enabled: boolean) => {
  await crawlerStore.toggleConfig(id, enabled)
}

const handleRun = async (id: string) => {
  await crawlerStore.runConfig(id)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (currentConfig.value) {
        await crawlerStore.updateConfig(currentConfig.value.id, form)
      } else {
        await crawlerStore.createConfig(form)
      }
      dialogVisible.value = false
    }
  })
}

onMounted(async () => {
  await crawlerStore.fetchConfigs()
})
</script>

<style scoped>
.crawler-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}
</style> 