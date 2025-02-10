<template>
  <div class="crawler-task-log">
    <div v-if="error" class="error-message" data-test="error-message">
      {{ error }}
    </div>

    <div class="log-header">
      <el-select
        v-model="levelFilter"
        placeholder="日志级别"
        data-test="level-filter"
        @change="handleLevelChange"
      >
        <el-option label="全部" value="" />
        <el-option label="INFO" value="INFO" />
        <el-option label="WARN" value="WARN" />
        <el-option label="ERROR" value="ERROR" />
      </el-select>

      <el-input
        v-model="searchKeyword"
        placeholder="搜索日志"
        data-test="search-input"
        @input="handleSearch"
      />

      <el-button
        type="primary"
        data-test="export-button"
        @click="handleExport"
      >
        导出日志
      </el-button>
    </div>

    <div v-if="loading" class="loading" data-test="loading">
      <el-loading />
    </div>

    <el-table
      v-loading="loading"
      :data="logs"
      class="log-table"
    >
      <el-table-column label="时间" prop="timestamp" width="180" />
      <el-table-column label="级别" width="100">
        <template #default="{ row }">
          <el-tag
            :type="getLevelType(row.level)"
            data-test="log-level"
          >
            {{ row.level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="消息" prop="message" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import type { TaskLog } from '@/types/crawler'

const props = defineProps<{
  taskId: string
}>()

const store = useCrawlerStore()
const loading = ref(false)
const error = ref<string | null>(null)
const logs = ref<TaskLog[]>([])
const levelFilter = ref('')
const searchKeyword = ref('')

onMounted(async () => {
  await fetchLogs()
})

const fetchLogs = async () => {
  try {
    loading.value = true
    const response = await store.fetchTaskLogs({
      taskId: props.taskId,
      level: levelFilter.value || undefined,
      keyword: searchKeyword.value || undefined,
      page: 1,
      pageSize: 10
    })
    logs.value = response.items
  } catch (err) {
    error.value = '获取日志失败'
    console.error('获取日志失败:', err)
  } finally {
    loading.value = false
  }
}

const handleLevelChange = async (level: string) => {
  levelFilter.value = level
  await fetchLogs()
}

const handleSearch = async (keyword: string) => {
  searchKeyword.value = keyword
  await fetchLogs()
}

const handleExport = async () => {
  try {
    loading.value = true
    await store.exportTaskLogs(props.taskId)
    ElMessage.success('导出成功')
  } catch (err) {
    error.value = '导出日志失败'
    console.error('导出日志失败:', err)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

const getLevelType = (level: string) => {
  const typeMap = {
    INFO: 'success',
    WARN: 'warning',
    ERROR: 'danger'
  }
  return typeMap[level] || 'info'
}
</script>

<style scoped>
.crawler-task-log {
  padding: 20px;
}

.log-header {
  margin-bottom: 20px;
  display: flex;
  gap: 16px;
}

.error-message {
  color: #f56c6c;
  margin-bottom: 16px;
}

.loading {
  text-align: center;
  margin: 20px 0;
}
</style> 