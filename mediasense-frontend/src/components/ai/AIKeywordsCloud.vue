<template>
  <div class="keywords-cloud" :style="{ width: width + 'px', height: height + 'px' }">
    <div v-if="loading" class="loading-container" data-test="loading">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else-if="error" class="error-container" data-test="error">
      <el-empty :description="error" />
      <el-button type="primary" @click="refreshData">重试</el-button>
    </div>
    <div v-else class="chart-container" ref="chartRef" data-test="keywords-cloud"></div>
    <div class="controls">
      <el-select v-model="selectedTimeRange" @change="handleTimeRangeChange">
        <el-option label="最近24小时" value="24h" />
        <el-option label="最近7天" value="7d" />
        <el-option label="最近30天" value="30d" />
      </el-select>
      <el-button @click="refreshData" :loading="loading" type="primary" size="small">
        刷新
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useAIStore } from '@/stores/ai'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import type { KeywordData } from '@/types/api'

const props = withDefaults(defineProps<{
  width?: number
  height?: number
  minFontSize?: number
  maxFontSize?: number
  colors?: string[]
}>(), {
  width: 800,
  height: 400,
  minFontSize: 12,
  maxFontSize: 60,
  colors: () => ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
})

const store = useAIStore()
const chartRef = ref<HTMLElement | null>(null)
const chart = ref<echarts.ECharts | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const selectedTimeRange = ref('24h')

const initChart = () => {
  if (!chartRef.value) return
  
  chart.value = echarts.init(chartRef.value)
  const option = {
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '90%',
      height: '90%',
      right: null,
      bottom: null,
      sizeRange: [props.minFontSize, props.maxFontSize],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: function () {
          return props.colors[Math.floor(Math.random() * props.colors.length)]
        }
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          shadowBlur: 10,
          shadowColor: '#333'
        }
      },
      data: []
    }]
  }
  chart.value.setOption(option)
}

const updateChart = (data: KeywordData[]) => {
  if (!chart.value) return
  
  chart.value.setOption({
    series: [{
      data: data.map(item => ({
        ...item,
        textStyle: {
          color: props.colors[Math.floor(Math.random() * props.colors.length)]
        }
      }))
    }]
  })
}

const fetchData = async () => {
  loading.value = true
  error.value = null
  try {
    const data = await store.fetchKeywords(selectedTimeRange.value)
    if (data) {
      updateChart(data)
    }
  } catch (err) {
    error.value = '获取关键词失败'
    console.error('获取关键词数据失败:', err)
  } finally {
    loading.value = false
  }
}

const handleTimeRangeChange = () => {
  fetchData()
}

const refreshData = () => {
  fetchData()
}

const handleResize = () => {
  chart.value?.resize()
}

onMounted(() => {
  initChart()
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart.value?.dispose()
  window.removeEventListener('resize', handleResize)
})

watch(
  () => [props.width, props.height],
  () => {
    chart.value?.resize()
  }
)
</script>

<style scoped>
.keywords-cloud {
  position: relative;
  background: #fff;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.chart-container {
  width: 100%;
  height: calc(100% - 40px);
}

.controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 1;
}
</style>