<template>
  <div class="crawler-task-list">
    <div class="task-header">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务"
        class="search-input"
        data-test="task-search"
        @input="handleSearch"
      />
      <el-select
        v-model="statusFilter"
        placeholder="状态筛选"
        data-test="status-filter"
        @change="handleFilterChange"
      >
        <el-option label="全部" value="" />
        <el-option label="运行中" value="running" />
        <el-option label="已停止" value="stopped" />
        <el-option label="错误" value="error" />
      </el-select>
      <div class="batch-actions">
        <el-button
          type="primary"
          :disabled="!selectedTasks.length"
          data-test="batch-start"
          @click="handleBatchStart"
        >
          批量启动
        </el-button>
        <el-button
          type="warning"
          :disabled="!selectedTasks.length"
          data-test="batch-stop"
          @click="handleBatchStop"
        >
          批量停止
        </el-button>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="tasks"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column label="任务名称" prop="name" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag
            :type="getStatusType(row.status)"
            data-test="task-status"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="200">
        <template #default="{ row }">
          <el-progress
            :percentage="getProgress(row)"
            :status="getProgressStatus(row.status)"
            data-test="task-progress"
          />
        </template>
      </el-table-column>
      <el-table-column label="运行时间" width="180">
        <template #default="{ row }">
          <span data-test="task-runtime">{{ formatTime(row.startTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="统计信息" width="200">
        <template #default="{ row }">
          <div data-test="task-stats">
            <div>成功: {{ row.successItems }}</div>
            <div>失败: {{ row.failedItems }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button
            v-if="row.status !== 'running'"
            type="primary"
            size="small"
            :data-test="'start-task-' + row.id"
            @click="handleStart(row)"
          >
            启动
          </el-button>
          <el-button
            v-else
            type="warning"
            size="small"
            :data-test="'stop-task-' + row.id"
            @click="handleStop(row)"
          >
            停止
          </el-button>
          <el-button
            type="danger"
            size="small"
            :data-test="'delete-task-' + row.id"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
          <el-button
            type="info"
            size="small"
            :data-test="'view-task-' + row.id"
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerTask } from '@/types/crawler'

const store = useCrawlerStore()
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')
const selectedTasks = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const tasks = ref<CrawlerTask[]>([])

const emit = defineEmits<{
  (e: 'view-detail', id: string): void
}>()

onMounted(async () => {
  await fetchTasks()
})

const fetchTasks = async () => {
  try {
    loading.value = true
    const response = await store.fetchTasks({
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value,
      status: statusFilter.value || undefined
    })
    tasks.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchTasks()
}

const handleSelectionChange = (selection: CrawlerTask[]) => {
  selectedTasks.value = selection.map(task => task.id)
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchTasks()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchTasks()
}

const handleStart = async (task: CrawlerTask) => {
  try {
    await store.startTask(task.id)
    ElMessage.success('启动任务成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('启动任务失败')
  }
}

const handleStop = async (task: CrawlerTask) => {
  try {
    await ElMessageBox.confirm('确定要停止该任务吗？')
    await store.stopTask(task.id)
    ElMessage.success('停止任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止任务失败')
    }
  }
}

const handleDelete = async (task: CrawlerTask) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？')
    await store.deleteTask(task.id)
    ElMessage.success('删除任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

const handleBatchStart = async () => {
  try {
    await store.batchStartTasks(selectedTasks.value)
    ElMessage.success('批量启动任务成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('批量启动任务失败')
  }
}

const handleBatchStop = async () => {
  try {
    await ElMessageBox.confirm('确定要批量停止选中的任务吗？')
    await store.batchStopTasks(selectedTasks.value)
    ElMessage.success('批量停止任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量停止任务失败')
    }
  }
}

const handleViewDetail = (task: CrawlerTask) => {
  emit('view-detail', task.id)
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return texts[status] || status
}

const getProgress = (task: CrawlerTask) => {
  if (task.totalItems === 0) return 0
  return Math.round((task.successItems / task.totalItems) * 100)
}

const getProgressStatus = (status: string) => {
  if (status === 'error') return 'exception'
  if (status === 'stopped') return ''
  return 'success'
}

const formatTime = (time?: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}
</script>

<style scoped>
.crawler-task-list {
  padding: 20px;
}

.task-header {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-input {
  width: 200px;
}

.batch-actions {
  margin-left: auto;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 