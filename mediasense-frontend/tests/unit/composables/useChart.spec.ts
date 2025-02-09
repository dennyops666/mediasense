import { describe, it, expect, beforeEach } from 'vitest'
import { useChart } from '@/composables/useChart'
import { ref } from 'vue'

describe('useChart', () => {
  let chart

  beforeEach(() => {
    chart = useChart()
  })

  describe('折线图配置', () => {
    it('应该生成正确的折线图配置', () => {
      const data = ref({
        xAxis: ['2024-03-01', '2024-03-02', '2024-03-03'],
        series: [10, 20, 30]
      })

      const options = chart.getLineChartOptions(data.value)

      expect(options).toMatchObject({
        xAxis: {
          type: 'category',
          data: ['2024-03-01', '2024-03-02', '2024-03-03']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          type: 'line',
          data: [10, 20, 30]
        }]
      })
    })

    it('应该支持多条数据线', () => {
      const data = ref({
        xAxis: ['2024-03-01', '2024-03-02'],
        series: [
          { name: '系列1', data: [10, 20] },
          { name: '系列2', data: [15, 25] }
        ]
      })

      const options = chart.getLineChartOptions(data.value)

      expect(options.series).toHaveLength(2)
      expect(options.series[0]).toMatchObject({
        name: '系列1',
        type: 'line',
        data: [10, 20]
      })
      expect(options.series[1]).toMatchObject({
        name: '系列2',
        type: 'line',
        data: [15, 25]
      })
    })
  })

  describe('饼图配置', () => {
    it('应该生成正确的饼图配置', () => {
      const data = ref([
        { name: '类别1', value: 30 },
        { name: '类别2', value: 70 }
      ])

      const options = chart.getPieChartOptions(data.value)

      expect(options).toMatchObject({
        series: [{
          type: 'pie',
          data: [
            { name: '类别1', value: 30 },
            { name: '类别2', value: 70 }
          ]
        }]
      })
    })
  })

  describe('柱状图配置', () => {
    it('应该生成正确的柱状图配置', () => {
      const data = ref({
        xAxis: ['类别1', '类别2', '类别3'],
        series: [10, 20, 30]
      })

      const options = chart.getBarChartOptions(data.value)

      expect(options).toMatchObject({
        xAxis: {
          type: 'category',
          data: ['类别1', '类别2', '类别3']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          type: 'bar',
          data: [10, 20, 30]
        }]
      })
    })
  })

  describe('图表主题', () => {
    it('应该支持自定义主题色', () => {
      const data = ref({
        xAxis: ['2024-03-01'],
        series: [10]
      })
      const theme = ['#ff0000', '#00ff00']

      const options = chart.getLineChartOptions(data.value, { colors: theme })

      expect(options.color).toEqual(theme)
    })
  })

  describe('图表工具箱', () => {
    it('应该支持导出功能', () => {
      const data = ref({
        xAxis: ['2024-03-01'],
        series: [10]
      })

      const options = chart.getLineChartOptions(data.value, { showToolbox: true })

      expect(options.toolbox).toBeDefined()
      expect(options.toolbox.feature.saveAsImage).toBeDefined()
    })
  })
})

