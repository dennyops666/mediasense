<template>
  <div class="system-monitor">
    <a-card title="系统资源监控" :loading="loading">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="refreshStats">
            刷新
          </a-button>
          <a-select
            v-model:value="refreshInterval"
            style="width: 120px"
            @change="handleIntervalChange"
          >
            <a-select-option :value="0">手动刷新</a-select-option>
            <a-select-option :value="5">5秒</a-select-option>
            <a-select-option :value="10">10秒</a-select-option>
            <a-select-option :value="30">30秒</a-select-option>
          </a-select>
        </a-space>
      </template>
      
      <!-- 系统资源使用情况 -->
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <template #title>
              <span>CPU使用率</span>
              <a-progress
                type="circle"
                :percent="stats.cpu?.percent || 0"
                :status="getProgressStatus(stats.cpu?.percent)"
                :width="80"
              />
            </template>
            <p>核心数: {{ stats.cpu?.count || 0 }}</p>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card>
            <template #title>
              <span>内存使用率</span>
              <a-progress
                type="circle"
                :percent="stats.memory?.percent || 0"
                :status="getProgressStatus(stats.memory?.percent)"
                :width="80"
              />
            </template>
            <p>
              已用: {{ formatBytes(stats.memory?.used) }} /
              总计: {{ formatBytes(stats.memory?.total) }}
            </p>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card>
            <template #title>
              <span>磁盘使用率</span>
              <a-progress
                type="circle"
                :percent="stats.disk?.percent || 0"
                :status="getProgressStatus(stats.disk?.percent)"
                :width="80"
              />
            </template>
            <p>
              已用: {{ formatBytes(stats.disk?.used) }} /
              总计: {{ formatBytes(stats.disk?.total) }}
            </p>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card>
            <template #title>
              <span>进程信息</span>
            </template>
            <p>进程数: {{ stats.process?.count || 0 }}</p>
            <p>线程数: {{ stats.process?.thread_count || 0 }}</p>
          </a-card>
        </a-col>
      </a-row>
      
      <!-- 告警信息 -->
      <a-card title="系统告警" style="margin-top: 16px">
        <template #extra>
          <a-button type="link" @click="showThresholdModal">
            配置告警阈值
          </a-button>
        </template>
        
        <a-table
          :dataSource="alerts"
          :columns="alertColumns"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'level'">
              <a-tag :color="getAlertColor(record.level)">
                {{ record.level }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-card>
    
    <!-- 告警阈值配置对话框 -->
    <a-modal
      v-model:visible="thresholdModalVisible"
      title="告警阈值配置"
      @ok="saveThresholds"
    >
      <a-form :model="thresholds" layout="vertical">
        <a-form-item label="CPU使用率阈值 (%)">
          <a-input-number
            v-model:value="thresholds.cpu_percent"
            :min="0"
            :max="100"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="内存使用率阈值 (%)">
          <a-input-number
            v-model:value="thresholds.memory_percent"
            :min="0"
            :max="100"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="磁盘使用率阈值 (%)">
          <a-input-number
            v-model:value="thresholds.disk_percent"
            :min="0"
            :max="100"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="进程数阈值">
          <a-input-number
            v-model:value="thresholds.process_count"
            :min="0"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
    
    <!-- 添加历史数据图表 -->
    <a-card title="资源使用趋势" style="margin-top: 16px">
      <template #extra>
        <a-select
          v-model:value="historyHours"
          style="width: 120px"
          @change="loadHistoryData"
        >
          <a-select-option :value="6">最近6小时</a-select-option>
          <a-select-option :value="12">最近12小时</a-select-option>
          <a-select-option :value="24">最近24小时</a-select-option>
        </a-select>
      </template>
      
      <a-row :gutter="16">
        <a-col :span="12">
          <div ref="cpuChart" style="height: 300px"></div>
        </a-col>
        <a-col :span="12">
          <div ref="memoryChart" style="height: 300px"></div>
        </a-col>
      </a-row>
      
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <div ref="diskChart" style="height: 300px"></div>
        </a-col>
        <a-col :span="12">
          <div ref="processChart" style="height: 300px"></div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import axios from 'axios'
import * as echarts from 'echarts'

export default defineComponent({
  name: 'SystemMonitor',
  
  setup() {
    const loading = ref(false)
    const stats = ref({})
    const alerts = ref([])
    const refreshInterval = ref(0)
    const refreshTimer = ref(null)
    const thresholdModalVisible = ref(false)
    const thresholds = ref({
      cpu_percent: 80,
      memory_percent: 80,
      disk_percent: 80,
      process_count: 500
    })
    
    // 告警表格列定义
    const alertColumns = [
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type'
      },
      {
        title: '级别',
        dataIndex: 'level',
        key: 'level'
      },
      {
        title: '信息',
        dataIndex: 'message',
        key: 'message'
      }
    ]
    
    // 获取系统统计信息
    const getStats = async () => {
      try {
        loading.value = true
        const response = await axios.get('/api/monitoring/stats/')
        stats.value = response.data.stats
        alerts.value = response.data.alerts
      } catch (error) {
        message.error('获取系统统计信息失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }
    
    // 刷新统计信息
    const refreshStats = () => {
      getStats()
    }
    
    // 处理刷新间隔变化
    const handleIntervalChange = (value) => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
      }
      
      if (value > 0) {
        refreshTimer.value = setInterval(refreshStats, value * 1000)
      }
    }
    
    // 获取进度条状态
    const getProgressStatus = (percent) => {
      if (!percent) return 'normal'
      if (percent >= 90) return 'exception'
      if (percent >= 70) return 'warning'
      return 'normal'
    }
    
    // 获取告警标签颜色
    const getAlertColor = (level) => {
      const colors = {
        error: 'red',
        warning: 'orange',
        info: 'blue'
      }
      return colors[level] || 'blue'
    }
    
    // 格式化字节数
    const formatBytes = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
    }
    
    // 显示阈值配置对话框
    const showThresholdModal = async () => {
      try {
        const response = await axios.get('/api/monitoring/alerts/thresholds/')
        thresholds.value = response.data
        thresholdModalVisible.value = true
      } catch (error) {
        message.error('获取告警阈值失败')
        console.error(error)
      }
    }
    
    // 保存告警阈值
    const saveThresholds = async () => {
      try {
        await axios.put('/api/monitoring/alerts/thresholds/', thresholds.value)
        message.success('告警阈值更新成功')
        thresholdModalVisible.value = false
      } catch (error) {
        message.error('更新告警阈值失败')
        console.error(error)
      }
    }
    
    // 添加新的响应式变量
    const historyHours = ref(6)
    const cpuChart = ref(null)
    const memoryChart = ref(null)
    const diskChart = ref(null)
    const processChart = ref(null)
    let charts = []
    
    // 加载历史数据
    const loadHistoryData = async () => {
      try {
        const response = await axios.get(`/api/monitoring/stats/history/?hours=${historyHours.value}`)
        const history = response.data.history
        
        // 处理数据
        const timestamps = history.map(item => item.timestamp)
        const cpuData = history.map(item => item.cpu?.percent || 0)
        const memoryData = history.map(item => item.memory?.percent || 0)
        const diskData = history.map(item => item.disk?.percent || 0)
        const processData = history.map(item => item.process?.count || 0)
        
        // 更新图表
        updateCharts(timestamps, cpuData, memoryData, diskData, processData)
      } catch (error) {
        message.error('加载历史数据失败')
        console.error(error)
      }
    }
    
    // 初始化图表
    const initCharts = () => {
      // CPU使用率图表
      const cpuChartInstance = echarts.init(cpuChart.value)
      cpuChartInstance.setOption({
        title: { text: 'CPU使用率趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{
          name: 'CPU使用率',
          type: 'line',
          smooth: true,
          areaStyle: {},
          data: []
        }]
      })
      
      // 内存使用率图表
      const memoryChartInstance = echarts.init(memoryChart.value)
      memoryChartInstance.setOption({
        title: { text: '内存使用率趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{
          name: '内存使用率',
          type: 'line',
          smooth: true,
          areaStyle: {},
          data: []
        }]
      })
      
      // 磁盘使用率图表
      const diskChartInstance = echarts.init(diskChart.value)
      diskChartInstance.setOption({
        title: { text: '磁盘使用率趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{
          name: '磁盘使用率',
          type: 'line',
          smooth: true,
          areaStyle: {},
          data: []
        }]
      })
      
      // 进程数图表
      const processChartInstance = echarts.init(processChart.value)
      processChartInstance.setOption({
        title: { text: '进程数趋势' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', min: 0 },
        series: [{
          name: '进程数',
          type: 'line',
          smooth: true,
          areaStyle: {},
          data: []
        }]
      })
      
      charts = [
        cpuChartInstance,
        memoryChartInstance,
        diskChartInstance,
        processChartInstance
      ]
      
      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        charts.forEach(chart => chart.resize())
      })
    }
    
    // 更新图表数据
    const updateCharts = (timestamps, cpuData, memoryData, diskData, processData) => {
      const [cpu, memory, disk, process] = charts
      
      // 更新CPU图表
      cpu.setOption({
        xAxis: { data: timestamps },
        series: [{
          data: cpuData.map((value, index) => [timestamps[index], value])
        }]
      })
      
      // 更新内存图表
      memory.setOption({
        xAxis: { data: timestamps },
        series: [{
          data: memoryData.map((value, index) => [timestamps[index], value])
        }]
      })
      
      // 更新磁盘图表
      disk.setOption({
        xAxis: { data: timestamps },
        series: [{
          data: diskData.map((value, index) => [timestamps[index], value])
        }]
      })
      
      // 更新进程图表
      process.setOption({
        xAxis: { data: timestamps },
        series: [{
          data: processData.map((value, index) => [timestamps[index], value])
        }]
      })
    }
    
    // 组件挂载时初始化图表并加载数据
    onMounted(() => {
      // 现有的初始化代码
      getStats()
      
      // 初始化图表
      initCharts()
      loadHistoryData()
    })
    
    // 组件卸载时清理资源
    onUnmounted(() => {
      // 现有的清理代码
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
      }
      
      // 销毁图表实例
      charts.forEach(chart => chart.dispose())
      window.removeEventListener('resize', () => {
        charts.forEach(chart => chart.resize())
      })
    })
    
    return {
      loading,
      stats,
      alerts,
      alertColumns,
      refreshInterval,
      thresholdModalVisible,
      thresholds,
      refreshStats,
      handleIntervalChange,
      getProgressStatus,
      getAlertColor,
      formatBytes,
      showThresholdModal,
      saveThresholds,
      historyHours,
      cpuChart,
      memoryChart,
      diskChart,
      processChart,
      loadHistoryData
    }
  }
})
</script>

<style scoped>
.system-monitor {
  padding: 24px;
}

.ant-card {
  margin-bottom: 16px;
}

.ant-progress {
  margin-top: 16px;
}
</style> 