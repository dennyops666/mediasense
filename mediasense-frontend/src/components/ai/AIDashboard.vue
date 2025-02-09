<template>
  <div class="ai-dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>API 使用情况</span>
              <el-button text @click="refreshUsage" data-test="refresh-button">刷新</el-button>
            </div>
          </template>
          <div v-loading="loading.usage" data-test="usage-loading">
            <el-statistic title="总调用次数" :value="usage.totalCalls" data-test="total-calls" />
            <el-statistic title="本月调用次数" :value="usage.monthCalls" data-test="month-calls" />
            <el-statistic title="剩余额度" :value="usage.remainingCredits" data-test="remaining-credits" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>模型性能</span>
            </div>
          </template>
          <div v-loading="loading.performance">
            <el-statistic title="平均响应时间" :value="performance.avgResponseTime" data-test="avg-response-time" :precision="2" suffix="ms" />
            <el-statistic title="成功率" :value="performance.successRate" data-test="success-rate" :precision="2" suffix="%" />
            <el-progress 
              :percentage="performance.successRate"
              :status="performance.successRate > 90 ? 'success' : 'warning'"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>任务统计</span>
            </div>
          </template>
          <div v-loading="loading.tasks">
            <el-statistic title="总任务数" :value="tasks.total" data-test="total-tasks" />
            <el-statistic title="成功任务" :value="tasks.success" data-test="success-tasks" />
            <el-statistic title="失败任务" :value="tasks.failed" data-test="failed-tasks" class="error-text" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>调用趋势</span>
              <el-select v-model="timeRange" size="small" @change="refreshTrend" data-test="time-range-select">
                <el-option label="最近7天" value="7d" />
                <el-option label="最近30天" value="30d" />
                <el-option label="最近90天" value="90d" />
              </el-select>
            </div>
          </template>
          <div ref="trendChart" class="chart-container" v-loading="loading.trend"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>模型使用分布</span>
            </div>
          </template>
          <div ref="modelChart" class="chart-container" v-loading="loading.models"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAIStore } from '@/stores/ai'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const store = useAIStore()

const usage = ref({
  totalCalls: null,
  monthCalls: null,
  remainingCredits: null
})

const performance = ref({
  avgResponseTime: null,
  successRate: null
})

const tasks = ref({
  total: null,
  success: null,
  failed: null
})

const timeRange = ref('7d')
const trendChart = ref<HTMLElement>()
const modelChart = ref<HTMLElement>()
let trendInstance: echarts.ECharts | null = null
let modelInstance: echarts.ECharts | null = null

const loading = ref({
  usage: false,
  performance: false,
  tasks: false,
  trend: false,
  models: false
})

const refreshUsage = async () => {
  loading.value.usage = true
  try {
    const data = await store.fetchUsage()
    if (data) {
      usage.value = {
        totalCalls: data.totalCalls || 0,
        monthCalls: data.monthCalls || 0,
        remainingCredits: data.remainingCredits || 0
      }
    }
  } catch (error) {
    console.error('获取使用统计失败:', error)
  } finally {
    loading.value.usage = false
  }
}

const refreshPerformance = async () => {
  loading.value.performance = true
  try {
    const data = await store.fetchPerformance()
    if (data) {
      performance.value = {
        avgResponseTime: data.avgResponseTime || 0,
        successRate: data.successRate || 0
      }
    }
  } catch (error) {
    console.error('获取性能统计失败:', error)
  } finally {
    loading.value.performance = false
  }
}

const refreshTasks = async () => {
  loading.value.tasks = true
  try {
    const data = await store.fetchTasks()
    if (data) {
      tasks.value = {
        total: data.total || 0,
        success: data.success || 0,
        failed: data.failed || 0
      }
    }
  } catch (error) {
    console.error('获取任务统计失败:', error)
  } finally {
    loading.value.tasks = false
  }
}

const refreshTrend = async () => {
  loading.value.trend = true
  try {
    const data = await store.fetchTrend(timeRange.value)
    if (trendInstance && data) {
      const option: EChartsOption = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: data.dates || []
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: data.values || [],
          type: 'line',
          smooth: true
        }]
      }
      trendInstance.setOption(option)
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  } finally {
    loading.value.trend = false
  }
}

const refreshModels = async () => {
  loading.value.models = true
  try {
    const data = await store.fetchModelUsage()
    if (modelInstance && data) {
      const option: EChartsOption = {
        tooltip: {
          trigger: 'item'
        },
        series: [{
          type: 'pie',
          radius: '60%',
          data: (data || []).map(item => ({
            name: item.model,
            value: item.count
          }))
        }]
      }
      modelInstance.setOption(option)
    }
  } catch (error) {
    console.error('获取模型使用数据失败:', error)
  } finally {
    loading.value.models = false
  }
}

const initCharts = () => {
  if (trendChart.value && !trendInstance) {
    trendInstance = echarts.init(trendChart.value)
  }
  if (modelChart.value && !modelInstance) {
    modelInstance = echarts.init(modelChart.value)
  }
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  trendInstance?.resize()
  modelInstance?.resize()
}

onMounted(async () => {
  initCharts()
  await Promise.all([
    refreshUsage(),
    refreshPerformance(),
    refreshTasks(),
    refreshTrend(),
    refreshModels()
  ])
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendInstance?.dispose()
  modelInstance?.dispose()
  trendInstance = null
  modelInstance = null
})
</script>

<style scoped>
.ai-dashboard {
  padding: 20px;
}

.dashboard-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.mt-20 {
  margin-top: 20px;
}

.error-text :deep(.el-statistic__content) {
  color: var(--el-color-danger);
}
</style> 