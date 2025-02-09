<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="(stat, index) in statistics" :key="index">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-icon">
            <el-icon :size="24" :color="stat.color">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>系统资源使用趋势</span>
              <el-radio-group v-model="timeRange" size="small">
                <el-radio-button label="day">今日</el-radio-button>
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container" ref="trendChartRef"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>告警分布</span>
            </div>
          </template>
          <div class="chart-container" ref="pieChartRef"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近告警 -->
    <el-card class="recent-alerts">
      <template #header>
        <div class="card-header">
          <span>最近告警</span>
          <el-button type="primary" link>查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentAlerts" style="width: 100%">
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getAlertLevelType(row.level)">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="150" />
        <el-table-column prop="message" label="告警信息" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已处理' ? 'success' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  Monitor,
  Warning,
  Connection,
  DataLine
} from '@element-plus/icons-vue'

const router = useRouter()
const timeRange = ref('day')
const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

// 统计数据
const statistics = [
  {
    label: '在线设备',
    value: '42',
    icon: Monitor,
    color: '#409EFF'
  },
  {
    label: '活跃告警',
    value: '3',
    icon: Warning,
    color: '#F56C6C'
  },
  {
    label: '网络连接',
    value: '89%',
    icon: Connection,
    color: '#67C23A'
  },
  {
    label: '系统负载',
    value: '65%',
    icon: DataLine,
    color: '#E6A23C'
  }
]

// 最近告警数据
const recentAlerts = [
  {
    time: '2024-03-20 10:30:45',
    level: '严重',
    source: 'Server-01',
    message: 'CPU使用率超过90%',
    status: '未处理'
  },
  {
    time: '2024-03-20 09:15:22',
    level: '警告',
    source: 'Server-02',
    message: '内存使用率超过80%',
    status: '已处理'
  },
  {
    time: '2024-03-20 08:45:10',
    level: '一般',
    source: 'Server-03',
    message: '磁盘使用率超过70%',
    status: '未处理'
  }
]

// 获取告警级别对应的标签类型
const getAlertLevelType = (level: string) => {
  const map: Record<string, string> = {
    '严重': 'danger',
    '警告': 'warning',
    '一般': 'info'
  }
  return map[level] || 'info'
}

// 初始化趋势图表
const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['CPU使用率', '内存使用率', '磁盘使用率']
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
      data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        data: [30, 35, 45, 60, 55, 65, 50, 45],
        smooth: true
      },
      {
        name: '内存使用率',
        type: 'line',
        data: [45, 50, 55, 65, 60, 70, 65, 60],
        smooth: true
      },
      {
        name: '磁盘使用率',
        type: 'line',
        data: [60, 62, 65, 68, 70, 72, 75, 78],
        smooth: true
      }
    ]
  }
  trendChart.setOption(option)
}

// 初始化饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  
  pieChart = echarts.init(pieChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '70%',
        data: [
          { value: 3, name: '严重', itemStyle: { color: '#F56C6C' } },
          { value: 5, name: '警告', itemStyle: { color: '#E6A23C' } },
          { value: 8, name: '一般', itemStyle: { color: '#909399' } }
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
  pieChart.setOption(option)
}

// 监听窗口大小变化
const handleResize = () => {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  initTrendChart()
  initPieChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  height: 100px;
}

.stat-icon {
  padding: 20px;
  border-radius: 8px;
  background-color: var(--el-color-primary-light-9);
}

.stat-info {
  margin-left: 20px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.stat-label {
  margin-top: 4px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.chart-row {
  margin-top: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 350px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-alerts {
  margin-top: 20px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 15px 20px;
}
</style> 