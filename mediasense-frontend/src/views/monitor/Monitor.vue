<template>
  <div class="monitor-container" data-test="monitor-container" v-loading="loading">
    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      data-test="error-alert"
      show-icon
      class="error-alert"
    />

    <!-- 系统指标卡片 -->
    <div class="metrics-grid">
      <el-card class="metric-card" data-test="cpu-card">
        <template #header>
          <div class="card-header">
            <span>CPU</span>
          </div>
        </template>
        <div class="metric-value" data-test="cpu-usage">
          {{ metrics?.cpu?.usage }}%
        </div>
        <div class="metric-detail" data-test="cpu-cores">
          核心数: {{ metrics?.cpu?.cores }}
        </div>
      </el-card>

      <el-card class="metric-card" data-test="memory-card">
        <template #header>
          <div class="card-header">
            <span>内存</span>
          </div>
        </template>
        <div class="metric-value" data-test="memory-usage">
          {{ metrics?.memory?.usagePercentage }}%
        </div>
        <div class="metric-detail">
          已用: {{ metrics?.memory?.used }} / {{ metrics?.memory?.total }}
        </div>
      </el-card>
    </div>

    <!-- 日志表格 -->
    <el-card class="log-card">
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
        </div>
      </template>
      <el-table :data="logs" data-test="logs-table">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            <span data-test="log-timestamp">{{ formatTime(row.timestamp) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : 'info'"
              :data-test="`log-level-${row.id}`"
            >
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息">
          <template #default="{ row }">
            <span data-test="log-message">{{ row.message }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 进程列表 -->
    <el-card class="process-card">
      <template #header>
        <div class="card-header">
          <span>进程列表</span>
          <el-input
            v-model="processFilter"
            placeholder="搜索进程"
            data-test="process-search"
          />
        </div>
      </template>
      <el-table :data="filteredProcesses" data-test="process-table">
        <el-table-column prop="pid" label="PID" width="100">
          <template #default="{ row }">
            <span data-test="process-pid">{{ row.pid }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称">
          <template #default="{ row }">
            <span data-test="process-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'RUNNING' ? 'success' : 'danger'"
              :data-test="`process-status-${row.pid}`"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'RUNNING'"
              type="danger"
              size="small"
              :data-test="`kill-process-${row.pid}`"
              @click="handleKillProcess(row.pid)"
            >
              终止
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useMonitorStore } from '@/stores/monitor'
import type { ProcessInfo, LogInfo } from '@/types/monitor'
import { formatTime } from '@/utils/time'

const store = useMonitorStore()
const loading = ref(false)
const error = computed(() => store.error)
const processFilter = ref('')

const metrics = computed(() => store.metrics)
const logs = computed(() => store.logs || [])

// 系统指标相关
const cpuUsage = computed(() => store.metrics?.cpu?.usage || 0)
const cpuCores = computed(() => store.metrics?.cpu?.cores || 0)
const totalMemory = computed(() => store.metrics?.memory?.total || 0)
const memoryUsage = computed(() => store.metrics?.memory?.usagePercentage || 0)

// 健康状态计算
const cpuHealthType = computed(() => {
  const usage = cpuUsage.value
  if (usage >= 90) return 'danger'
  if (usage >= 70) return 'warning'
  return 'success'
})

const memoryHealthType = computed(() => {
  const usage = memoryUsage.value
  if (usage >= 90) return 'danger'
  if (usage >= 70) return 'warning'
  return 'success'
})

const cpuStatusText = computed(() => {
  const usage = cpuUsage.value
  if (usage >= 90) return '严重'
  if (usage >= 70) return '警告'
  return '正常'
})

const memoryStatusText = computed(() => {
  const usage = memoryUsage.value
  if (usage >= 90) return '严重'
  if (usage >= 70) return '警告'
  return '正常'
})

// 进程相关
const filteredProcesses = computed(() => {
  const processes = store.processes || []
  if (!processFilter.value) {
    return processes
  }
  return processes.filter(process => 
    process.name.toLowerCase().includes(processFilter.value.toLowerCase()) ||
    process.pid.toString().includes(processFilter.value)
  )
})

// 格式化内存大小
const formatMemory = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const value = bytes / Math.pow(1024, i)
  return `${value.toFixed(2)} ${units[i]}`
}

// 获取进程状态类型
const getProcessStatusType = (status: string): string => {
  if (!status) return ''
  const statusMap: Record<string, string> = {
    running: 'success',
    stopped: 'danger',
    sleeping: 'warning',
    zombie: 'danger',
    waiting: 'info'
  }
  return statusMap[status.toLowerCase()] || ''
}

// 刷新方法
const refreshSystemMetrics = async () => {
  try {
    loading.value = true
    error.value = null
    await store.fetchSystemMetrics()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '获取系统指标失败'
  } finally {
    loading.value = false
  }
}

const refreshLogs = async () => {
  try {
    loading.value = true
    error.value = null
    await store.fetchSystemLogs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '获取日志失败'
  } finally {
    loading.value = false
  }
}

const refreshProcessList = async () => {
  try {
    loading.value = true
    error.value = null
    await store.fetchProcessList()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '获取进程列表失败'
  } finally {
    loading.value = false
  }
}

// 终止进程
const handleKillProcess = async (pid: number) => {
  try {
    await ElMessageBox.confirm(`确定要终止进程 ${pid} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await store.killProcess(pid)
    await store.fetchProcessList()
    ElMessage.success('进程已终止')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(`终止进程失败：${err instanceof Error ? err.message : String(err)}`)
    }
  }
}

// 生命周期钩子
const refreshInterval = ref<number | null>(null)

onMounted(async () => {
  try {
    await Promise.all([
      store.fetchSystemMetrics(),
      store.fetchSystemLogs(),
      store.fetchProcessList()
    ])
    await store.startMonitoring()
  } catch (err) {
    console.error('初始化监控失败:', err)
  }
  
  store.startMonitoring()
  refreshInterval.value = window.setInterval(() => {
    refreshSystemMetrics()
    refreshProcessList()
  }, 5000)
})

onUnmounted(() => {
  store.stopMonitoring()
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
})
</script>

<style scoped>
.monitor-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-alert {
  margin-bottom: 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.metric-card {
  text-align: center;
}

.metric-value {
  font-size: 2em;
  font-weight: bold;
  margin: 10px 0;
}

.metric-detail {
  color: #666;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.process-card :deep(.el-input) {
  width: 200px;
}
</style> 