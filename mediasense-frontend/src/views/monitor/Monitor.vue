<template>
  <div class="monitor-page">
    <el-row :gutter="20">
      <!-- 系统概览 -->
      <el-col :span="24">
        <el-card class="overview-card">
          <template #header>
            <div class="card-header">
              <h2>系统概览</h2>
              <el-button-group>
                <el-button
                  v-for="period in periods"
                  :key="period.value"
                  :type="currentPeriod === period.value ? 'primary' : ''"
                  @click="currentPeriod = period.value"
                >
                  {{ period.label }}
                </el-button>
              </el-button-group>
            </div>
          </template>

          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon cpu">
                  <el-icon><cpu /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">CPU 使用率</div>
                  <div class="stat-value">{{ cpuUsage }}%</div>
                </div>
              </div>
            </el-col>

            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon memory">
                  <el-icon><monitor /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">内存使用率</div>
                  <div class="stat-value">{{ memoryUsage }}%</div>
                </div>
              </div>
            </el-col>

            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon disk">
                  <el-icon><files /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">磁盘使用率</div>
                  <div class="stat-value">{{ diskUsage }}%</div>
                </div>
              </div>
            </el-col>

            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon process">
                  <el-icon><operation /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-label">进程数</div>
                  <div class="stat-value">{{ processCount }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- CPU 使用率趋势 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>CPU 使用率趋势</h3>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="cpuChartOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <!-- 内存使用率趋势 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>内存使用率趋势</h3>
            </div>
          </template>
          <div class="chart-container">
            <v-chart class="chart" :option="memoryChartOption" autoresize />
          </div>
        </el-card>
      </el-col>

      <!-- 系统日志 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>系统日志</h3>
              <el-button-group>
                <el-button
                  v-for="level in logLevels"
                  :key="level.value"
                  :type="currentLogLevel === level.value ? 'primary' : ''"
                  @click="currentLogLevel = level.value"
                >
                  {{ level.label }}
                </el-button>
              </el-button-group>
            </div>
          </template>

          <el-table
            :data="logs"
            style="width: 100%"
            max-height="400"
            v-loading="loading"
          >
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLogLevelType(row.level)">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="150" />
            <el-table-column prop="message" label="消息" />
          </el-table>

          <div class="table-footer">
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
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import type { ECBasicOption } from 'echarts/types/dist/shared'
import VChart from 'vue-echarts'
import { formatDate } from '@/utils/date'
import {
  Monitor,
  Files,
  Operation,
  Cpu
} from '@element-plus/icons-vue'
import type { SystemLog } from '@/types/api'
import * as monitorApi from '@/api/monitor'
import { ElMessage } from 'element-plus'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
])

// 时间周期选项
const periods = [
  { label: '实时', value: 'realtime' },
  { label: '1小时', value: '1h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' }
] as const

type PeriodValue = typeof periods[number]['value']
const currentPeriod = ref<PeriodValue>('realtime')

// 日志级别选项
const logLevels = [
  { label: '全部', value: 'all' },
  { label: '错误', value: 'error' },
  { label: '警告', value: 'warning' },
  { label: '信息', value: 'info' }
] as const

type LogLevel = typeof logLevels[number]['value']
const currentLogLevel = ref<LogLevel>('all')

// 系统指标
const cpuUsage = ref(0)
const memoryUsage = ref(0)
const diskUsage = ref(0)
const processCount = ref(0)

// 图表数据
interface ChartOption extends ECBasicOption {
  tooltip: {
    trigger: 'axis'
  }
  grid: {
    left: string
    right: string
    bottom: string
    containLabel: boolean
  }
  xAxis: {
    type: 'category'
    boundaryGap: boolean
    data: string[]
  }
  yAxis: {
    type: 'value'
    max: number
    min: number
  }
  series: Array<{
    name: string
    type: 'line'
    data: number[]
    smooth: boolean
    showSymbol: boolean
    areaStyle: {
      opacity: number
    }
  }>
}

const cpuChartOption = ref<ChartOption>({
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
    data: []
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
      data: [],
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
})

const memoryChartOption = ref<ChartOption>({
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
    data: []
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
      data: [],
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
})

// 日志相关
const logs = ref<SystemLog[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      level: currentLogLevel.value === 'all' ? undefined : currentLogLevel.value
    }
    const { total: totalCount, items } = await monitorApi.getSystemLogs(params)
    logs.value = items
    total.value = totalCount
  } catch (error) {
    ElMessage.error('获取系统日志失败')
  } finally {
    loading.value = false
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

// 监听日志级别变化
watch(currentLogLevel, () => {
  currentPage.value = 1 // 重置页码
  fetchLogs()
})

const getLogLevelType = (level: SystemLog['level']) => {
  const types: Record<SystemLog['level'], string> = {
    error: 'danger',
    warning: 'warning',
    info: 'info'
  }
  return types[level]
}

const updateChartData = (timeStr: string, cpuValue: number, memoryValue: number) => {
  // 更新 CPU 图表数据
  cpuChartOption.value.xAxis.data.push(timeStr)
  cpuChartOption.value.series[0].data.push(cpuValue)
  if (cpuChartOption.value.xAxis.data.length > 60) {
    cpuChartOption.value.xAxis.data.shift()
    cpuChartOption.value.series[0].data.shift()
  }

  // 更新内存图表数据
  memoryChartOption.value.xAxis.data.push(timeStr)
  memoryChartOption.value.series[0].data.push(memoryValue)
  if (memoryChartOption.value.xAxis.data.length > 60) {
    memoryChartOption.value.xAxis.data.shift()
    memoryChartOption.value.series[0].data.shift()
  }
}

const updateMetrics = async () => {
  try {
    const data = await monitorApi.getSystemMetrics()
    const now = new Date()
    const timeStr = now.toLocaleTimeString()
    
    cpuUsage.value = Math.round(data.cpuUsage)
    memoryUsage.value = Math.round(data.memoryUsage)
    diskUsage.value = Math.round(data.diskUsage)
    processCount.value = data.processCount
    
    updateChartData(timeStr, data.cpuUsage, data.memoryUsage)
  } catch (error) {
    console.error('获取系统指标失败:', error)
  }
}

// 定时更新数据
let timer: number | null = null

onMounted(async () => {
  // 初始化加载日志
  await fetchLogs()
  
  // 初始化系统指标
  await updateMetrics()
  
  // 定时更新系统指标
  timer = window.setInterval(updateMetrics, 2000)
})

onUnmounted(() => {
  if (timer !== null) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.monitor-page {
  padding: 20px;
}

.overview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2,
.card-header h3 {
  margin: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: var(--el-bg-color-page);
  border-radius: var(--el-border-radius-base);
}

.stat-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  margin-right: 16px;
  font-size: 24px;
}

.stat-icon.cpu {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.stat-icon.memory {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.stat-icon.disk {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.stat-icon.process {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.chart-container {
  height: 300px;
}

.chart {
  height: 100%;
}

.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-card) {
  margin-bottom: 20px;
}

:deep(.el-table) {
  margin-top: 16px;
}
</style> 