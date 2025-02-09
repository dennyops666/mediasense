<template>
  <div class="crawler-list">
    <!-- 顶部操作栏 -->
    <div class="operation-bar">
      <el-button-group>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新建任务
        </el-button>
        <el-button type="success" @click="handleBatchStart" :disabled="!selectedTasks.length">
          <el-icon><VideoPlay /></el-icon>批量启动
        </el-button>
        <el-button type="danger" @click="handleBatchStop" :disabled="!selectedTasks.length">
          <el-icon><VideoPause /></el-icon>批量停止
        </el-button>
      </el-button-group>

      <div class="filter-group">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索任务名称"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="filterStatus" placeholder="任务状态" clearable @change="handleSearch">
          <el-option label="运行中" value="running" />
          <el-option label="已停止" value="stopped" />
          <el-option label="出错" value="error" />
        </el-select>
      </div>
    </div>

    <!-- 任务列表 -->
    <el-table
      v-loading="loading"
      :data="taskList"
      @selection-change="handleSelectionChange"
      style="width: 100%"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="任务名称" min-width="200">
        <template #default="{ row }">
          <div class="task-name">
            <el-icon :class="row.status"><component :is="getStatusIcon(row.status)" /></el-icon>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="爬虫类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="schedule" label="调度规则" width="150" />
      <el-table-column prop="lastRunTime" label="最后运行" width="180">
        <template #default="{ row }">
          {{ formatDate(row.lastRunTime) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="count" label="采集数量" width="120">
        <template #default="{ row }">
          {{ row.count }} 条
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button
              :type="row.status === 'running' ? 'danger' : 'success'"
              :icon="row.status === 'running' ? 'VideoPause' : 'VideoPlay'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'running' ? '停止' : '启动' }}
            </el-button>
            <el-button type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button type="info" @click="handleViewData(row)">
              <el-icon><View /></el-icon>数据
            </el-button>
            <el-button type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
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

    <!-- 新建/编辑任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTask ? '编辑任务' : '新建任务'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="taskForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="爬虫类型" prop="type">
          <el-select v-model="taskForm.type" placeholder="请选择爬虫类型">
            <el-option label="新闻" value="news" />
            <el-option label="社交媒体" value="social" />
            <el-option label="网站" value="website" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度规则" prop="schedule">
          <el-input v-model="taskForm.schedule" placeholder="Cron表达式">
            <template #append>
              <el-tooltip content="Cron表达式帮助">
                <el-button @click="showCronHelper">
                  <el-icon><Question /></el-icon>
                </el-button>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="配置参数" prop="config">
          <el-input
            v-model="taskForm.config"
            type="textarea"
            :rows="6"
            placeholder="请输入JSON格式的配置参数"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveTask">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 数据预览对话框 -->
    <el-dialog
      v-model="dataPreviewVisible"
      title="数据预览"
      width="80%"
    >
      <el-table
        :data="previewData"
        height="500"
        border
        style="width: 100%"
      >
        <el-table-column
          v-for="col in previewColumns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
        />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  VideoPlay,
  VideoPause,
  Edit,
  View,
  Delete,
  Question
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import type { CrawlerTask, TaskStatus } from '@/types/crawler'
import { useCrawlerStore } from '@/stores/crawler'

const store = useCrawlerStore()

// 状态变量
const loading = ref(false)
const searchKeyword = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedTasks = ref<CrawlerTask[]>([])
const dialogVisible = ref(false)
const dataPreviewVisible = ref(false)
const editingTask = ref<CrawlerTask | null>(null)
const taskList = ref<CrawlerTask[]>([])
const previewData = ref([])
const previewColumns = ref([])

// 表单相关
const formRef = ref()
const taskForm = ref({
  name: '',
  type: '',
  schedule: '',
  config: ''
})

const rules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择爬虫类型', trigger: 'change' }
  ],
  schedule: [
    { required: true, message: '请输入调度规则', trigger: 'blur' }
  ],
  config: [
    { required: true, message: '请输入配置参数', trigger: 'blur' }
  ]
}

// 获取任务列表
const fetchTaskList = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value,
      status: filterStatus.value
    }
    const { data, total: totalCount } = await store.fetchTasks(params)
    taskList.value = data
    total.value = totalCount
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 状态图标
const getStatusIcon = (status: TaskStatus) => {
  const iconMap = {
    running: 'VideoPlay',
    stopped: 'VideoPause',
    error: 'Warning'
  }
  return iconMap[status]
}

// 状态类型
const getStatusType = (status: TaskStatus) => {
  const typeMap = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[status]
}

// 事件处理
const handleAdd = () => {
  editingTask.value = null
  taskForm.value = {
    name: '',
    type: '',
    schedule: '',
    config: ''
  }
  dialogVisible.value = true
}

const handleEdit = (task: CrawlerTask) => {
  editingTask.value = task
  taskForm.value = {
    name: task.name,
    type: task.type,
    schedule: task.schedule,
    config: JSON.stringify(task.config, null, 2)
  }
  dialogVisible.value = true
}

const handleSaveTask = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    const taskData = {
      ...taskForm.value,
      config: JSON.parse(taskForm.value.config)
    }
    
    if (editingTask.value) {
      await store.updateTask(editingTask.value.id, taskData)
      ElMessage.success('任务更新成功')
    } else {
      await store.createTask(taskData)
      ElMessage.success('任务创建成功')
    }
    
    dialogVisible.value = false
    fetchTaskList()
  } catch (error) {
    if (error instanceof Error) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('操作失败')
    }
  }
}

const handleToggleStatus = async (task: CrawlerTask) => {
  try {
    if (task.status === 'running') {
      await store.stopTask(task.id)
      ElMessage.success('任务已停止')
    } else {
      await store.startTask(task.id)
      ElMessage.success('任务已启动')
    }
    fetchTaskList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (task: CrawlerTask) => {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？', '警告', {
      type: 'warning'
    })
    await store.deleteTask(task.id)
    ElMessage.success('任务已删除')
    fetchTaskList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleViewData = async (task: CrawlerTask) => {
  try {
    const { data, columns } = await store.fetchTaskData(task.id)
    previewData.value = data
    previewColumns.value = columns
    dataPreviewVisible.value = true
  } catch (error) {
    ElMessage.error('获取数据失败')
  }
}

const handleBatchStart = async () => {
  try {
    await ElMessageBox.confirm('确定要启动选中的任务吗？', '提示')
    const ids = selectedTasks.value.map(task => task.id)
    await store.batchStartTasks(ids)
    ElMessage.success('任务已启动')
    fetchTaskList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleBatchStop = async () => {
  try {
    await ElMessageBox.confirm('确定要停止选中的任务吗？', '提示')
    const ids = selectedTasks.value.map(task => task.id)
    await store.batchStopTasks(ids)
    ElMessage.success('任务已停止')
    fetchTaskList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleSelectionChange = (selection: CrawlerTask[]) => {
  selectedTasks.value = selection
}

const handleSearch = () => {
  currentPage.value = 1
  fetchTaskList()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchTaskList()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchTaskList()
}

const showCronHelper = () => {
  // TODO: 实现Cron表达式帮助对话框
}

// 初始化
onMounted(() => {
  fetchTaskList()
})
</script>

<style scoped>
.crawler-list {
  padding: 20px;
}

.operation-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-group {
  display: flex;
  gap: 16px;
}

.task-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-name .el-icon {
  font-size: 16px;
}

.task-name .running {
  color: var(--el-color-success);
}

.task-name .stopped {
  color: var(--el-color-info);
}

.task-name .error {
  color: var(--el-color-danger);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.alert-detail {
  padding: 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.detail-item {
  margin-bottom: 10px;
  display: flex;
  gap: 8px;
}

.detail-item .label {
  color: var(--el-text-color-secondary);
  width: 80px;
}

.detail-item .value {
  color: var(--el-text-color-primary);
  flex: 1;
}
</style> 