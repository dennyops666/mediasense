<template>
  <div class="crawler-task-list">
    <div class="search-filter">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务名称"
        data-test="search-input"
        clearable
        @input="handleSearch"
      />
      <el-select
        v-model="statusFilter"
        placeholder="任务状态"
        data-test="status-filter"
        clearable
        @change="handleFilterChange"
      >
        <el-option label="运行中" value="running" />
        <el-option label="已停止" value="stopped" />
        <el-option label="错误" value="error" />
      </el-select>
    </div>

    <div class="batch-actions">
      <el-button
        type="primary"
        data-test="batch-start-button"
        :disabled="selectedTasks.length === 0"
        @click="handleBatchStart"
      >
        批量启动
      </el-button>
      <el-button
        type="warning"
        data-test="batch-stop-button"
        :disabled="selectedTasks.length === 0"
        @click="handleBatchStop"
      >
        批量停止
      </el-button>
    </div>

    <div v-if="error" class="error-message" data-test="error-message">
      {{ error }}
    </div>

    <el-table
      v-loading="loading"
      :data="tasks"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="任务名称">
        <template #default="scope">
          <div class="task-name">{{ scope.row.name }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)" data-test="task-status">
            {{ getStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="180">
        <template #default="scope">
          <el-progress
            :percentage="getProgress(scope.row)"
            :status="getProgressStatus(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button
            v-if="scope.row.status !== 'running'"
            type="primary"
            size="small"
            data-test="start-button"
            @click="handleStart(scope.row)"
          >
            启动
          </el-button>
          <el-button
            v-else
            type="warning"
            size="small"
            data-test="stop-button"
            @click="handleStop(scope.row)"
          >
            停止
          </el-button>
          <el-button
            type="danger"
            size="small"
            data-test="delete-button"
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerTask } from '@/types/crawler'

const store = useCrawlerStore()
const searchKeyword = ref('')
const statusFilter = ref('')
const selectedTasks = ref<CrawlerTask[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

const tasks = computed(() => store.tasks)
const total = computed(() => store.total)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

const fetchTasks = async () => {
  await store.fetchTasks({
    keyword: searchKeyword.value,
    status: statusFilter.value,
    page: currentPage.value,
    pageSize: pageSize.value
  })
}

const handleSearch = async () => {
  currentPage.value = 1
  await fetchTasks()
}

const handleFilterChange = async () => {
  currentPage.value = 1
  await fetchTasks()
}

const handleCurrentChange = async (page: number) => {
  currentPage.value = page
  await fetchTasks()
}

const handleStart = async (task: CrawlerTask) => {
  try {
    await store.startTask(task.id)
    ElMessage.success('启动任务成功')
    await fetchTasks()
  } catch (err) {
    ElMessage.error('启动任务失败')
  }
}

const handleStop = async (task: CrawlerTask) => {
  try {
    await ElMessageBox.confirm('确定要停止该任务吗？', '提示', {
      type: 'warning'
    })
    await store.stopTask(task.id)
    ElMessage.success('停止任务成功')
    await fetchTasks()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('停止任务失败')
    }
  }
}

const handleDelete = async (task: CrawlerTask) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '提示', {
      type: 'warning'
    })
    await store.deleteTask(task.id)
    ElMessage.success('删除任务成功')
    await fetchTasks()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

const handleBatchStart = async () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请选择要启动的任务')
    return
  }

  try {
    await store.batchStartTasks(selectedTasks.value.map(task => task.id))
    ElMessage.success('批量启动成功')
    await fetchTasks()
  } catch (err) {
    ElMessage.error('批量启动失败')
  }
}

const handleBatchStop = async () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请选择要停止的任务')
    return
  }

  try {
    await ElMessageBox.confirm('确定要批量停止选中的任务吗？', '提示', {
      type: 'warning'
    })
    await store.batchStopTasks(selectedTasks.value.map(task => task.id))
    ElMessage.success('批量停止成功')
    await fetchTasks()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('批量停止失败')
    }
  }
}

const handleSelectionChange = (selection: CrawlerTask[]) => {
  selectedTasks.value = selection
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return textMap[status] || status
}

const getProgress = (task: CrawlerTask) => {
  if (!task.totalItems) return 0
  return Math.round((task.successItems / task.totalItems) * 100)
}

const getProgressStatus = (task: CrawlerTask) => {
  if (task.status === 'error') return 'exception'
  if (task.status === 'running') return ''
  return 'success'
}

onMounted(async () => {
  await fetchTasks()
})

defineExpose({
  tasks: store.tasks,
  total: store.total,
  loading,
  error,
  searchKeyword,
  statusFilter,
  selectedTasks,
  currentPage,
  pageSize,
  handleSearch,
  handleFilterChange,
  handleCurrentChange,
  handleStart,
  handleStop,
  handleDelete,
  handleBatchStart,
  handleBatchStop,
  handleSelectionChange
})
</script>

<style scoped>
.crawler-task-list {
  padding: 20px;
}

.search-filter {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.batch-actions {
  margin-bottom: 20px;
}

.error-message {
  color: #f56c6c;
  margin-bottom: 16px;
}

.task-name {
  font-weight: 500;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 