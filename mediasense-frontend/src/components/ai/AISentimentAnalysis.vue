<template>
  <div class="ai-sentiment-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>情感分析</span>
          <div class="header-actions">
            <el-select
              v-model="timeRange"
              size="small"
              @change="handleTimeRangeChange"
            >
              <el-option label="最近24小时" value="24h" />
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
              <el-option label="全部" value="all" />
            </el-select>
            <el-button 
              type="primary" 
              size="small"
              :loading="loading"
              @click="handleRefresh"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="analysis-content" v-loading="loading">
        <div class="overview-section">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="sentiment-card positive">
                <div class="sentiment-icon">
                  <el-icon><SmileFilled /></el-icon>
                </div>
                <div class="sentiment-info">
                  <div class="sentiment-label">正面情感</div>
                  <div class="sentiment-value">{{ stats.positive }}%</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="sentiment-card neutral">
                <div class="sentiment-icon">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="sentiment-info">
                  <div class="sentiment-label">中性情感</div>
                  <div class="sentiment-value">{{ stats.neutral }}%</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="sentiment-card negative">
                <div class="sentiment-icon">
                  <el-icon><WarnTriangleFilled /></el-icon>
                </div>
                <div class="sentiment-info">
                  <div class="sentiment-label">负面情感</div>
                  <div class="sentiment-value">{{ stats.negative }}%</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="chart-section">
          <el-tabs v-model="activeChart">
            <el-tab-pane label="趋势图" name="trend">
              <div ref="trendChart" class="chart-container"></div>
            </el-tab-pane>
            <el-tab-pane label="分布图" name="distribution">
              <div ref="distributionChart" class="chart-container"></div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <div class="details-section">
          <el-table
            :data="tableData"
            style="width: 100%"
            :max-height="300"
            border
          >
            <el-table-column prop="time" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column prop="sentiment" label="情感倾向" width="120">
              <template #default="{ row }">
                <el-tag :type="getSentimentType(row.sentiment)">
                  {{ getSentimentLabel(row.sentiment) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="100">
              <template #default="{ row }">
                {{ formatScore(row.score) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { SmileFilled, CircleCheck, WarnTriangleFilled } from '@element-plus/icons-vue'
import type { EChartsOption } from 'echarts'

interface SentimentStats {
  positive: number
  neutral: number
  negative: number
}

interface SentimentData {
  time: string
  content: string
  sentiment: 'positive' | 'neutral' | 'negative'
  score: number
}

interface Props {
  stats: SentimentStats
  data: SentimentData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  stats: () => ({
    positive: 0,
    neutral: 0,
    negative: 0
  }),
  data: () => [],
  loading: false
})

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'timeRangeChange', range: string): void
}>()

const timeRange = ref('24h')
const activeChart = ref('trend')
const trendChart = ref<HTMLElement>()
const distributionChart = ref<HTMLElement>()
let trendInstance: echarts.ECharts | null = null
let distributionInstance: echarts.ECharts | null = null

const tableData = computed(() => props.data.slice(0, 100))

const initCharts = () => {
  if (trendChart.value) {
    trendInstance = echarts.init(trendChart.value)
    updateTrendChart()
  }
  
  if (distributionChart.value) {
    distributionInstance = echarts.init(distributionChart.value)
    updateDistributionChart()
  }
}

const updateTrendChart = () => {
  if (!trendInstance) return

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: ['正面', '中性', '负面']
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
      data: props.data.map(item => formatDate(item.time))
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '正面',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.sentiment === 'positive' ? item.score : 0)
      },
      {
        name: '中性',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.sentiment === 'neutral' ? item.score : 0)
      },
      {
        name: '负面',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.data.map(item => item.sentiment === 'negative' ? item.score : 0)
      }
    ]
  }

  trendInstance.setOption(option)
}

const updateDistributionChart = () => {
  if (!distributionInstance) return

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '情感分布',
        type: 'pie',
        radius: '50%',
        data: [
          { value: props.stats.positive, name: '正面' },
          { value: props.stats.neutral, name: '中性' },
          { value: props.stats.negative, name: '负面' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  distributionInstance.setOption(option)
}

const handleResize = () => {
  trendInstance?.resize()
  distributionInstance?.resize()
}

const handleRefresh = () => {
  emit('refresh')
}

const handleTimeRangeChange = (value: string) => {
  emit('timeRangeChange', value)
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

const formatScore = (score: number) => {
  return (score * 100).toFixed(1) + '%'
}

const getSentimentType = (sentiment: string) => {
  const typeMap: Record<string, string> = {
    positive: 'success',
    neutral: 'info',
    negative: 'danger'
  }
  return typeMap[sentiment] || 'info'
}

const getSentimentLabel = (sentiment: string) => {
  const labelMap: Record<string, string> = {
    positive: '正面',
    neutral: '中性',
    negative: '负面'
  }
  return labelMap[sentiment] || '未知'
}

watch(() => props.data, () => {
  updateTrendChart()
  updateDistributionChart()
}, { deep: true })

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendInstance?.dispose()
  distributionInstance?.dispose()
})
</script>

<style scoped>
.ai-sentiment-analysis {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.analysis-content {
  padding: 20px 0;
}

.overview-section {
  margin-bottom: 30px;
}

.sentiment-card {
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.sentiment-card.positive {
  background-color: var(--el-color-success-light-9);
}

.sentiment-card.neutral {
  background-color: var(--el-color-info-light-9);
}

.sentiment-card.negative {
  background-color: var(--el-color-danger-light-9);
}

.sentiment-icon {
  font-size: 24px;
}

.positive .sentiment-icon {
  color: var(--el-color-success);
}

.neutral .sentiment-icon {
  color: var(--el-color-info);
}

.negative .sentiment-icon {
  color: var(--el-color-danger);
}

.sentiment-info {
  flex: 1;
}

.sentiment-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 5px;
}

.sentiment-value {
  font-size: 24px;
  font-weight: bold;
}

.chart-section {
  margin: 30px 0;
}

.chart-container {
  height: 400px;
}

.details-section {
  margin-top: 30px;
}
</style>
