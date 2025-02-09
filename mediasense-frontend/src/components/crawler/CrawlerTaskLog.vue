<template>
  <div class="crawler-task-log">
    <div class="log-header">
      <el-select
        v-model="levelFilter"
        placeholder="日志级别"
        data-test="level-filter"
        @change="handleLevelChange"
      >
        <el-option label="全部" value="" />
        <el-option label="INFO" value="INFO" />
        <el-option label="ERROR" value="ERROR" />
        <el-option label="WARNING" value="WARNING" />
      </el-select>

      <el-input
        v-model="searchKeyword"
        data-test="search-input"
        placeholder="搜索日志"
        @input="handleSearch"
      />

      <div class="log-actions">
        <el-button
          type="primary"
          :loading="exporting"
          data-test="export-button"
          @click="handleExport"
        >
          导出日志
        </el-button>
      </div>
    </div>

    <el-alert
      v-if="error"
      data-test="error-message"
      :title="error"
      type="error"
      show-icon
    />

    <div v-if="loading" data-test="loading">
      <el-skeleton :rows="3" animated />
    </div>

    <el-table
      v-else
      :data="logs"
      height="500"
      data-test="log-table"
    >
      <el-table-column label="时间" width="180">
        <template #default="{ row }">
          <span data-test="log-time">{{ formatTime(row.timestamp) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="级别" width="100">
        <template #default="{ row }">
          <el-tag
            :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : 'info'"
            data-test="log-level"
          >
            {{ row.level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="消息">
        <template #default="{ row }">
          <div data-test="log-message">{{ row.message }}</div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button
            type="text"
            data-test="view-detail"
            @click="handleViewDetail(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="日志详情"
      width="600px"
      data-test="log-detail-dialog"
    >
      <pre class="log-detail">{{ selectedLog?.metadata || '{}' }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerTaskLog } from '@/types/crawler'
import { formatTime } from '@/utils/time'

const props = defineProps<{
  taskId: string
}>()

const store = useCrawlerStore()
const loading = ref(false)
const exporting = ref(false)
const error = ref<string | null>(null)
const levelFilter = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const logs = ref<CrawlerTaskLog[]>([])
const detailVisible = ref(false)
const selectedLog = ref<CrawlerTaskLog | null>(null)
let refreshTimer: number | null = null

onMounted(async () => {
  await fetchLogs()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})

const fetchLogs = async () => {
  try {
    loading.value = true
    error.value = null
    await store.fetchTaskLogs({
      taskId: props.taskId,
      level: levelFilter.value,
      keyword: searchKeyword.value
    })
  } catch (err) {
    error.value = '获取日志失败'
    console.error('获取日志失败:', err)
  } finally {
    loading.value = false
  }
}

const handleLevelChange = (level: string) => {
  levelFilter.value = level
  fetchLogs()
}

const handleSearch = (keyword: string) => {
  searchKeyword.value = keyword
  fetchLogs()
}

const handleExport = async () => {
  try {
    exporting.value = true
    await store.exportTaskLogs(props.taskId)
    ElMessage.success('导出成功')
  } catch (err) {
    error.value = '导出日志失败'
    console.error('导出日志失败:', err)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchLogs()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchLogs()
}

const handleViewDetail = (log: CrawlerTaskLog) => {
  selectedLog.value = log
  detailVisible.value = true
}

watch(() => props.taskId, fetchLogs)
</script>

<style scoped>
.crawler-task-log {
  padding: 20px;
}

.log-header {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  align-items: center;
}

.log-actions {
  margin-left: auto;
  display: flex;
  gap: 16px;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.log-detail {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
}
</style> 