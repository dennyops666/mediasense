<template>
  <div class="system-resource-monitor">
    <div v-if="loading" class="loading">
      <div class="loading-spinner">
        <span>加载中...</span>
      </div>
    </div>
    <!-- CPU监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><cpu /></el-icon>
          <span>CPU监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value cpu-usage">{{ resources.cpu.usage.toFixed(1) }}%</span>
          <el-alert
            v-if="resources.cpu.usage > 80"
            type="warning"
            class="resource-alert"
            :title="`CPU使用率过高: ${resources.cpu.usage}%`"
            show-icon
          />
        </div>
        <div class="metric">
          <span class="label">核心数</span>
          <span class="value">{{ resources.cpu.cores }}</span>
        </div>
        <div class="metric">
          <span class="label">温度</span>
          <span class="value cpu-temperature">{{ resources.cpu.temperature }}°C</span>
        </div>
      </div>
      <div class="chart-container">
        <v-chart class="chart" :option="cpuChartOption" autoresize />
      </div>
    </el-card>

    <!-- 内存监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><monitor /></el-icon>
          <span>内存监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value memory-usage">{{ memoryUsagePercentage }}%</span>
          <el-alert
            v-if="memoryUsagePercentage > 90"
            type="warning"
            class="resource-alert"
            :title="`内存使用率过高: ${memoryUsagePercentage}%`"
            show-icon
          />
        </div>
        <div class="metric">
          <span class="label">总容量</span>
          <span class="value memory-total">{{ formatMemorySize(resources.memory.total) }}</span>
        </div>
        <div class="metric">
          <span class="label">剩余</span>
          <span class="value">{{ formatMemorySize(resources.memory.free) }}</span>
        </div>
      </div>
      <div class="chart-container">
        <v-chart class="chart" :option="memoryChartOption" autoresize />
      </div>
    </el-card>

    <!-- 磁盘监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><files /></el-icon>
          <span>磁盘监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value disk-usage">{{ diskUsagePercentage }}%</span>
          <el-alert
            v-if="diskUsagePercentage > 90"
            type="warning"
            class="resource-alert"
            :title="`磁盘空间不足: ${diskUsagePercentage}%`"
            show-icon
          />
        </div>
        <div class="metric">
          <span class="label">总容量</span>
          <span class="value disk-total">{{ formatDiskSize(resources.disk.total) }}</span>
        </div>
        <div class="metric">
          <span class="label">剩余</span>
          <span class="value">{{ formatDiskSize(resources.disk.free) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 网络监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><connection /></el-icon>
          <span>网络监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">上传速度</span>
          <span class="value network-upload">{{ formatNetworkSpeed(resources.network.tx_bytes) }}</span>
        </div>
        <div class="metric">
          <span class="label">下载速度</span>
          <span class="value network-download">{{ formatNetworkSpeed(resources.network.rx_bytes) }}</span>
        </div>
        <div class="metric">
          <span class="label">延迟</span>
          <span class="value">{{ resources.network.latency }}ms</span>
          <el-alert
            v-if="resources.network.latency > 150"
            type="warning"
            class="resource-alert"
            :title="`网络延迟过高: ${resources.network.latency}ms`"
            show-icon
          />
        </div>
      </div>
    </el-card>

    <!-- 最后更新时间 -->
    <div class="update-info">
      <span class="last-update">最后更新: {{ lastUpdate }}</span>
      <el-button type="primary" class="refresh-btn" @click="handleRefresh">刷新</el-button>
      <el-button class="alert-history-btn" @click="handleShowHistory">告警历史</el-button>
      <el-button class="export-btn" @click="handleExport">导出数据</el-button>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      type="error"
      :title="error"
      class="error-message"
      show-icon
    >
      <template #default>
        <el-button type="primary" size="small" @click="handleRetry">
          重试
        </el-button>
      </template>
    </el-alert>

    <!-- 告警历史对话框 -->
    <el-dialog
      v-model="showHistory"
      title="告警历史"
      width="60%"
      class="alert-history-dialog"
    >
      <el-table :data="alerts" stripe class="alert-history-table">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ new Date(scope.row.timestamp).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.level === 'critical' ? 'danger' : 'warning'">
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" />
      </el-table>
      <template v-if="!alerts.length">
        <el-empty description="暂无告警记录" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import type { SystemMetrics } from '@/types/monitor'
import {
  Monitor,
  Connection,
  Files,
  Cpu
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { ECOption } from '@/types/chart'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
])

const props = defineProps<{
  resources: SystemMetrics
  lastUpdate: string
  error: string | null
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'export'): void
}>()

const store = useMonitorStore()
const showHistory = ref(false)
const alerts = computed(() => store.alerts)

// 计算属性
const memoryUsagePercentage = computed(() => {
  const { total, used } = props.resources.memory
  return total ? Math.round((used / total) * 100) : 0
})

const diskUsagePercentage = computed(() => {
  const { total, used } = props.resources.disk
  return total ? Math.round((used / total) * 100) : 0
})

// 格式化函数
const formatMemorySize = (bytes: number) => {
  if (!bytes) return '0.0 GB'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)} GB`
}

const formatDiskSize = (bytes: number) => {
  if (!bytes) return '0.0 GB'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)} GB`
}

const formatNetworkSpeed = (bytesPerSecond: number) => {
  if (!bytesPerSecond) return '0.00 KB/s'
  if (bytesPerSecond < 1024) {
    return `${bytesPerSecond.toFixed(2)} B/s`
  } else if (bytesPerSecond < 1024 * 1024) {
    return `${(bytesPerSecond / 1024).toFixed(2)} KB/s`
  } else {
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(2)} MB/s`
  }
}

// 图表配置
const cpuChartOption = computed<ECOption>(() => ({
  tooltip: {
    trigger: 'axis'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: store.cpuHistory?.map(item => item.timestamp) || []
  },
  yAxis: {
    type: 'value',
    max: 100,
    min: 0
  },
  series: [
    {
      name: 'CPU使用率',
      type: 'line',
      data: store.cpuHistory?.map(item => item.value) || [],
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
}))

const memoryChartOption = computed<ECOption>(() => ({
  tooltip: {
    trigger: 'axis'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: store.memoryHistory?.map(item => item.timestamp) || []
  },
  yAxis: {
    type: 'value',
    max: 100,
    min: 0
  },
  series: [
    {
      name: '内存使用率',
      type: 'line',
      data: store.memoryHistory?.map(item => item.value) || [],
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
}))

// 事件处理
const handleRefresh = () => {
  emit('refresh')
}

const handleExport = () => {
  emit('export')
}

const handleShowHistory = () => {
  showHistory.value = true
}

const handleRetry = () => {
  emit('refresh')
}

// 生命周期
onMounted(() => {
  store.startMonitoring()
})

onUnmounted(() => {
  store.stopMonitoring()
})
</script>

<style scoped>
.system-resource-monitor {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
  position: relative;
}

.loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.loading-spinner::before {
  content: '';
  width: 32px;
  height: 32px;
  border: 3px solid var(--el-color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.monitor-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.chart-container {
  height: 200px;
}

.chart {
  height: 100%;
}

.update-info {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

:deep(.el-alert) {
  margin-top: 8px;
}
</style> 