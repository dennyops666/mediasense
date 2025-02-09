<template>
  <div class="monitor-container" data-test="monitor-container">
    <!-- 加载状态 -->
    <div v-loading="loading" data-test="loading-container">
      <!-- 错误信息 -->
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        closable
        @close="error = null"
        data-test="error-alert"
      />

      <!-- 系统指标卡片 -->
      <div class="metrics-grid">
        <!-- CPU状态卡片 -->
        <el-card class="monitor-card" data-test="cpu-card">
          <template #header>
            <div class="card-header">
              <span>CPU状态</span>
              <el-tag 
                :type="cpuHealthStatus"
                data-test="cpu-health"
              >
                {{ cpuStatusText }}
              </el-tag>
            </div>
          </template>
          <div class="metric-content">
            <el-row :gutter="20">
              <el-col :span="12">
                <div class="metric-item">
                  <div class="metric-label">使用率</div>
                  <div class="metric-value" data-test="cpu-usage">{{ cpuUsage }}%</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="metric-item">
                  <div class="metric-label">核心数</div>
                  <div class="metric-value" data-test="cpu-cores">{{ cpuCores }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>

        <!-- 内存状态卡片 -->
        <el-card class="monitor-card" data-test="memory-card">
          <template #header>
            <div class="card-header">
              <span>内存状态</span>
              <el-tag 
                :type="memoryHealthStatus"
                data-test="memory-health"
              >
                {{ memoryStatusText }}
              </el-tag>
            </div>
          </template>
          <div class="metric-content">
            <el-row :gutter="20">
              <el-col :span="12">
                <div class="metric-item">
                  <div class="metric-label">使用率</div>
                  <div class="metric-value" data-test="memory-usage">{{ memoryUsage }}%</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="metric-item">
                  <div class="metric-label">总内存</div>
                  <div class="metric-value" data-test="total-memory">{{ formatMemory(totalMemory) }}</div>
                </div>
              </el-col>
            </el-row>
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
                data-test="refresh-logs-button"
              >
                刷新
              </el-button>
            </div>
          </template>
          <el-table :data="logs" stripe>
            <el-table-column prop="timestamp" label="时间" width="180" />
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag 
                  v-if="row && row.level"
                  :type="getLogLevelType(row.level)"
                  :data-test="'log-level-' + row.level.toLowerCase()"
                >
                  {{ row.level }}
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
                  data-test="refresh-process-button"
                >
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          <el-table :data="filteredProcessList" stripe>
            <el-table-column prop="pid" label="PID" width="100" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="user" label="用户" width="120" />
            <el-table-column prop="cpu" label="CPU %" width="100" />
            <el-table-column prop="memory" label="内存" width="120">
              <template #default="{ row }">
                <span v-if="row && row.memory">{{ formatMemory(row.memory) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag 
                  v-if="row && row.status"
                  :type="getProcessStatusType(row.status)"
                  :data-test="'process-status-' + row.status.toLowerCase()"
                >
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button 
                  v-if="row && row.pid"
                  type="danger" 
                  size="small"
                  @click="handleKillProcess(row)"
                  :disabled="loading"
                  :data-test="'kill-process-' + row.pid"
                >
                  终止
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
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

// 日志相关
const logs = ref<LogInfo[]>([])

const refreshLogs = async () => {
  try {
    loading.value = true
    error.value = null
    const data = await store.fetchLogs()
    logs.value = data || []
  } catch (err) {
    error.value = '获取日志失败'
    console.error('获取日志失败:', err)
  } finally {
    loading.value = false
  }
}

const getLogLevelType = (level: string | undefined) => {
  if (!level) return ''
  switch (level.toLowerCase()) {
    case 'error': return 'danger'
    case 'warning': return 'warning'
    case 'info': return 'info'
    default: return ''
  }
}

// 进程相关
const processSearch = ref('')
const processList = ref<ProcessInfo[]>([])

const filteredProcessList = computed(() => {
  if (!processSearch.value) return processList.value
  const keyword = processSearch.value.toLowerCase()
  return processList.value.filter(process => 
    (process.name?.toLowerCase().includes(keyword) || false) ||
    (process.user?.toLowerCase().includes(keyword) || false)
  )
})

const refreshProcessList = async () => {
  try {
    loading.value = true
    error.value = null
    const data = await store.fetchProcessList()
    processList.value = data || []
  } catch (err) {
    error.value = '获取进程列表失败'
    console.error('获取进程列表失败:', err)
  } finally {
    loading.value = false
  }
}

const getProcessStatusType = (status: string | undefined) => {
  if (!status) return ''
  switch (status.toLowerCase()) {
    case 'running': return 'success'
    case 'stopped': return 'danger'
    case 'sleeping': return 'warning'
    default: return ''
  }
}

const handleKillProcess = async (process: ProcessInfo) => {
  if (!process?.pid) return
  
  try {
    await ElMessageBox.confirm('确定要终止该进程吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    error.value = null
    await store.killProcess(process.pid)
    ElMessage.success('进程已终止')
    await refreshProcessList()
  } catch (err) {
    if (err === 'cancel') return
    error.value = '终止进程失败'
    console.error('终止进程失败:', err)
    ElMessage.error('终止进程失败')
  } finally {
    loading.value = false
  }
}

// 系统指标相关
const cpuUsage = ref(0)
const cpuCores = ref(0)
const cpuLoad = ref(0)
const totalMemory = ref(0)
const usedMemory = ref(0)
const memoryUsage = ref(0)

const refreshSystemMetrics = async () => {
  try {
    loading.value = true
    error.value = null
    const metrics = await store.fetchSystemMetrics()
    if (metrics) {
      cpuUsage.value = metrics.cpu?.usage || 0
      cpuCores.value = metrics.cpu?.cores || 0
      cpuLoad.value = metrics.cpu?.load?.[0] || 0
      totalMemory.value = metrics.memory?.total || 0
      usedMemory.value = metrics.memory?.used || 0
      memoryUsage.value = metrics.memory?.usage || 0
    }
  } catch (err) {
    error.value = '获取系统指标失败'
    console.error('获取系统指标失败:', err)
  } finally {
    loading.value = false
  }
}

const cpuHealthStatus = computed(() => {
  if (cpuUsage.value >= 90) return 'danger'
  if (cpuUsage.value >= 70) return 'warning'
  return 'success'
})

const memoryHealthStatus = computed(() => {
  if (memoryUsage.value >= 90) return 'danger'
  if (memoryUsage.value >= 70) return 'warning'
  return 'success'
})

const cpuStatusText = computed(() => {
  if (cpuUsage.value >= 90) return '严重'
  if (cpuUsage.value >= 70) return '警告'
  return '正常'
})

const memoryStatusText = computed(() => {
  if (memoryUsage.value >= 90) return '严重'
  if (memoryUsage.value >= 70) return '警告'
  return '正常'
})

const formatMemory = (bytes: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

// 自动刷新
let refreshTimer: NodeJS.Timer | null = null

const startAutoRefresh = () => {
  refreshTimer = setInterval(refreshSystemMetrics, 5000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期钩子
onMounted(async () => {
  await Promise.all([
    refreshSystemMetrics(),
    refreshLogs(),
    refreshProcessList()
  ])
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
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