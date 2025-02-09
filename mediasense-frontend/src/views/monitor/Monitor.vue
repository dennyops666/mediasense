<template>
  <div class="monitor-container" data-test="monitor-container" v-loading="loading">
    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      data-test="error-alert"
    />

    <div class="metrics-grid">
      <!-- CPU 卡片 -->
      <el-card class="monitor-card" data-test="cpu-card">
        <template #header>
          <div class="card-header">
            <span>CPU 状态</span>
            <el-tag
              :type="cpuHealthType"
              data-test="cpu-health-status"
            >
              {{ cpuStatusText }}
            </el-tag>
          </div>
        </template>
        <div class="metric-content">
          <div class="metric-item">
            <div class="metric-label">使用率</div>
            <div class="metric-value" data-test="cpu-usage">{{ cpuUsage }}%</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">核心数</div>
            <div class="metric-value" data-test="cpu-cores">{{ cpuCores }}</div>
          </div>
        </div>
      </el-card>

      <!-- 内存卡片 -->
      <el-card class="monitor-card" data-test="memory-card">
        <template #header>
          <div class="card-header">
            <span>内存状态</span>
            <el-tag
              :type="memoryHealthType"
              data-test="memory-health-status"
            >
              {{ memoryStatusText }}
            </el-tag>
          </div>
        </template>
        <div class="metric-content">
          <div class="metric-item">
            <div class="metric-label">使用率</div>
            <div class="metric-value" data-test="memory-usage">{{ memoryUsage }}%</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">总内存</div>
            <div class="metric-value" data-test="total-memory">{{ formatMemory(totalMemory) }}</div>
          </div>
        </div>
      </el-card>

      <!-- 日志卡片 -->
      <el-card class="monitor-card" data-test="logs-card">
        <template #header>
          <div class="card-header">
            <span>系统日志</span>
            <el-button
              type="primary"
              @click="refreshLogs"
              :loading="loading"
              data-test="refresh-logs"
            >
              刷新
            </el-button>
          </div>
        </template>
        <el-table :data="logs" stripe data-test="logs-table">
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag
                v-if="row && row.level"
                :type="getLogLevelType(row.level)"
                :data-test="`log-level-${(row.level || 'unknown').toLowerCase()}`"
              >
                {{ row.level || 'UNKNOWN' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" />
        </el-table>
      </el-card>

      <!-- 进程列表 -->
      <el-card class="monitor-card" data-test="process-card">
        <template #header>
          <div class="card-header">
            <span>进程列表</span>
            <div class="header-actions">
              <el-input
                v-model="processSearch"
                placeholder="搜索进程"
                prefix-icon="Search"
                clearable
                style="width: 200px; margin-right: 10px;"
                data-test="process-search"
              />
              <el-button
                type="primary"
                @click="refreshProcessList"
                :loading="loading"
                data-test="refresh-processes"
              >
                刷新
              </el-button>
            </div>
          </div>
        </template>
        <el-table :data="filteredProcessList" stripe data-test="process-table">
          <el-table-column prop="pid" label="PID" width="100" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="user" label="用户" width="120" />
          <el-table-column prop="cpu" label="CPU %" width="100" />
          <el-table-column prop="memory" label="内存" width="120">
            <template #default="{ row }">
              <span v-if="row" data-test="process-memory">{{ formatMemory(row.memory || 0) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                v-if="row && row.status"
                :type="getProcessStatusType(row.status)"
                :data-test="`process-status-${(row.status || '').toLowerCase()}`"
              >
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                v-if="row"
                type="danger"
                size="small"
                @click="handleKillProcess(row.pid)"
                :disabled="loading"
                :data-test="`kill-process-${row.pid}`"
              >
                终止
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useMonitorStore } from '@/stores/monitor'
import type { ProcessInfo, LogInfo } from '@/types/monitor'

const store = useMonitorStore()
const loading = ref(false)
const error = ref<string | null>(null)
const processSearch = ref('')
const processList = ref<ProcessInfo[]>([])

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

// 日志相关
const logs = computed(() => store.logs || [])

const getLogLevelType = (level: string): string => {
  if (!level) return ''
  const levelMap: Record<string, string> = {
    error: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return levelMap[level.toLowerCase()] || ''
}

// 进程相关
const filteredProcessList = computed(() => {
  if (!processSearch.value) return store.processList || []
  const searchTerm = processSearch.value.toLowerCase()
  return (store.processList || []).filter(process => 
    process.name.toLowerCase().includes(searchTerm)
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
    await ElMessageBox.confirm('确定要终止该进程吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    error.value = null
    await store.killProcess(pid)
    ElMessage.success('进程已终止')
    await refreshProcessList()
  } catch (e) {
    if (e !== 'cancel') {
      error.value = e instanceof Error ? e.message : '终止进程失败'
      ElMessage.error(error.value)
    }
  } finally {
    loading.value = false
  }
}

// 生命周期钩子
const refreshInterval = ref<number | null>(null)

onMounted(async () => {
  await Promise.all([
    refreshSystemMetrics(),
    refreshLogs(),
    refreshProcessList()
  ])
  
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
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.monitor-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.metric-content {
  padding: 10px;
}

.metric-item {
  text-align: center;
  padding: 10px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
</style> 