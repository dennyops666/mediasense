import { ref } from 'vue'
import type { EChartsOption } from 'echarts'
import { ECBasicOption } from 'echarts/types/dist/shared'

export function useChart() {
  const chartTheme = ref({
    colors: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
  })

  const getLineChartOptions = (data: any, options: { colors?: string[], showToolbox?: boolean } = {}): ECBasicOption => {
    if (!data || !data.xAxis || !data.series) {
      console.warn('Invalid line chart data format')
      return {
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value' },
        series: []
      }
    }

    const baseOptions: ECBasicOption = {
      xAxis: {
        type: 'category',
        data: data.xAxis
      },
      yAxis: {
        type: 'value'
      }
    }

    if (options.colors) {
      baseOptions.color = options.colors
    }

    if (options.showToolbox) {
      baseOptions.toolbox = {
        feature: {
          saveAsImage: {}
        }
      }
    }

    // 处理单个数据系列和多个数据系列的情况
    if (Array.isArray(data.series) && typeof data.series[0] === 'object') {
      baseOptions.series = data.series.map(item => ({
        name: item.name,
        type: 'line',
        data: item.data
      }))
    } else {
      baseOptions.series = [{
        type: 'line',
        data: data.series
      }]
    }

    return baseOptions
  }

  const getPieChartOptions = (data: any[]): ECBasicOption => {
    if (!Array.isArray(data)) {
      console.warn('Pie chart data must be an array')
      return {
        series: [{
          type: 'pie',
          data: []
        }]
      }
    }

    return {
      series: [{
        type: 'pie',
        data: data
      }]
    }
  }

  const getBarChartOptions = (data: any): ECBasicOption => {
    if (!data || !data.xAxis || !data.series) {
      console.warn('Invalid bar chart data format')
      return {
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value' },
        series: [{ type: 'bar', data: [] }]
      }
    }

    return {
      xAxis: {
        type: 'category',
        data: data.xAxis
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        type: 'bar',
        data: data.series
      }]
    }
  }

  const setChartTheme = (colors: string[]) => {
    chartTheme.value.colors = colors
  }

  return {
    getLineChartOptions,
    getPieChartOptions,
    getBarChartOptions,
    setChartTheme,
    chartTheme
  }
}


