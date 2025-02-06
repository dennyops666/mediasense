<template>
  <div class="monitor-chart">
    <div class="chart-header">
      <h3>{{ title }}</h3>
      <div class="chart-actions">
        <el-radio-group v-model="currentPeriod" size="small">
          <el-radio-button
            v-for="period in periods"
            :key="period.value"
            :label="period.value"
          >
            {{ period.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div class="chart-container">
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
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
  title: string
  data: Array<{
    timestamp: string
    value: number
  }>
  unit?: string
  min?: number
  max?: number
}>()

const emit = defineEmits<{
  (e: 'period-change', period: string): void
}>()

// 时间周期选项
const periods = [
  { label: '实时', value: 'realtime' },
  { label: '1小时', value: '1h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' }
] as const

type PeriodValue = typeof periods[number]['value']
const currentPeriod = ref<PeriodValue>('realtime')

// 图表配置
const chartOption = computed<ECOption>(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const [param] = params
      return `${param.name}<br/>${param.value}${props.unit || ''}`
    }
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
    data: props.data.map(item => item.timestamp)
  },
  yAxis: {
    type: 'value',
    min: props.min,
    max: props.max,
    axisLabel: {
      formatter: `{value}${props.unit || ''}`
    }
  },
  series: [
    {
      type: 'line',
      data: props.data.map(item => item.value),
      smooth: true,
      showSymbol: false,
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
}))

// 监听周期变化
watch(currentPeriod, (newPeriod) => {
  emit('period-change', newPeriod)
})
</script>

<style scoped>
.monitor-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.chart-container {
  flex: 1;
  min-height: 200px;
}

.chart {
  height: 100%;
}
</style> 