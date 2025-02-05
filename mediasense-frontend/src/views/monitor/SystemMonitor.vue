<template>
  <div class="monitor-container">
    <!-- CPU监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><cpu-icon /></el-icon>
          <span>CPU监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value" data-test="cpu-usage">{{ currentMetrics.cpu?.usage?.toFixed(1) }}%</span>
        </div>
        <div class="metric">
          <span class="label">核心数</span>
          <span class="value" data-test="cpu-cores">{{ currentMetrics.cpu?.cores }}</span>
        </div>
        <div class="metric">
          <span class="label">温度</span>
          <span class="value" data-test="cpu-temp">{{ currentMetrics.cpu?.temperature }}°C</span>
        </div>
      </div>
    </el-card>

    <!-- 内存监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><memory-icon /></el-icon>
          <span>内存监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value" data-test="memory-usage">{{ formatMemoryUsage(currentMetrics.memory) }}%</span>
        </div>
        <div class="metric">
          <span class="label">总容量</span>
          <span class="value" data-test="memory-total">{{ formatMemorySize(currentMetrics.memory?.total) }}</span>
        </div>
        <div class="metric">
          <span class="label">剩余</span>
          <span class="value" data-test="memory-free">{{ formatMemorySize(currentMetrics.memory?.free) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 磁盘监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><disk-icon /></el-icon>
          <span>磁盘监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">使用率</span>
          <span class="value" data-test="disk-usage">{{ formatDiskUsage(currentMetrics.disk) }}%</span>
        </div>
        <div class="metric">
          <span class="label">总容量</span>
          <span class="value" data-test="disk-total">{{ formatDiskSize(currentMetrics.disk?.total) }}</span>
        </div>
        <div class="metric">
          <span class="label">剩余</span>
          <span class="value" data-test="disk-free">{{ formatDiskSize(currentMetrics.disk?.free) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 网络监控 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><connection-icon /></el-icon>
          <span>网络监控</span>
        </div>
      </template>
      <div class="metrics">
        <div class="metric">
          <span class="label">下载速度</span>
          <span class="value" data-test="network-rx">{{ formatNetworkSpeed(currentMetrics.network?.rx_bytes) }}</span>
        </div>
        <div class="metric">
          <span class="label">上传速度</span>
          <span class="value" data-test="network-tx">{{ formatNetworkSpeed(currentMetrics.network?.tx_bytes) }}</span>
        </div>
        <div class="metric">
          <span class="label">连接数</span>
          <span class="value" data-test="network-conn">{{ currentMetrics.network?.connections }}</span>
        </div>
      </div>
    </el-card>

    <!-- 服务状态 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><service-icon /></el-icon>
          <span>服务状态</span>
        </div>
      </template>
      <div class="services">
        <div
          v-for="service in currentServices"
          :key="service.name"
          class="service-item"
          :data-test="'service-' + service.name"
        >
          <div class="service-info">
            <span class="service-name">{{ service.name }}</span>
            <el-tag
              :type="getServiceStatusType(service.status)"
              class="service-status"
            >
              {{ service.status }}
            </el-tag>
          </div>
          <div class="service-meta">
            <span>运行时间: {{ service.uptime }}</span>
            <span>最后检查: {{ formatDate(service.lastCheck) }}</span>
          </div>
          <div class="service-actions">
            <el-button
              v-if="service.status === 'stopped'"
              type="primary"
              size="small"
              data-test="restart-service-btn"
              @click="handleRestartService(service.name)"
            >
              重启服务
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 告警信息 -->
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon><warning-icon /></el-icon>
          <span>告警信息</span>
        </div>
      </template>
      <div class="alerts">
        <div
          v-for="alert in currentAlerts"
          :key="alert.id"
          class="alert-item"
          :data-test="'alert-' + alert.id"
        >
          <div class="alert-header">
            <el-tag
              :type="getAlertLevelType(alert.level)"
              class="alert-level"
            >
              {{ alert.level }}
            </el-tag>
            <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
          </div>
          <div class="alert-message">{{ alert.message }}</div>
          <div class="alert-actions">
            <el-button
              type="primary"
              size="small"
              data-test="acknowledge-alert-btn"
              @click="handleAcknowledgeAlert(alert.id)"
            >
              确认告警
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'
import {
  Monitor as MonitorIcon,
  Cpu as CpuIcon,
  Connection as ConnectionIcon,
  Warning as WarningIcon,
  Setting as ServiceIcon,
  DataLine as MemoryIcon,
  Disk as DiskIcon
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'

const monitorStore = useMonitorStore()

const currentMetrics = computed(() => monitorStore.metrics || {
  cpu: {
    usage: 0,
    cores: 0,
    temperature: 0
  },
  memory: {
    total: 0,
    used: 0,
    free: 0
  },
  disk: {
    total: 0,
    used: 0,
    free: 0
  },
  network: {
    rx_bytes: 0,
    tx_bytes: 0,
    connections: 0
  }
})

const currentServices = computed(() => monitorStore.services || [])
const currentAlerts = computed(() => monitorStore.alerts || [])
let updateTimer: ReturnType<typeof setInterval>

// 获取系统指标
const fetchMetrics = async () => {
  try {
    await monitorStore.fetchSystemMetrics()
  } catch (error) {
    console.error('获取系统指标失败:', error)
    ElMessage.error('获取系统指标失败')
  }
}

// 获取服务状态
const fetchServices = async () => {
  try {
    await monitorStore.fetchServiceStatus()
  } catch (error) {
    console.error('获取服务状态失败:', error)
    ElMessage.error('获取服务状态失败')
  }
}

// 获取告警信息
const fetchAlerts = async () => {
  try {
    await monitorStore.fetchAlerts()
  } catch (error) {
    console.error('获取告警信息失败:', error)
    ElMessage.error('获取告警信息失败')
  }
}

// 重启服务
const handleRestartService = async (serviceName: string) => {
  try {
    await monitorStore.restartService(serviceName)
    ElMessage.success('服务已重启')
    await fetchServices()
  } catch (error) {
    console.error('重启服务失败:', error)
    ElMessage.error('重启服务失败')
  }
}

// 确认告警
const handleAcknowledgeAlert = async (alertId: string) => {
  try {
    await monitorStore.acknowledgeAlert(alertId)
    ElMessage.success('告警已确认')
    await fetchAlerts()
  } catch (error) {
    console.error('确认告警失败:', error)
    ElMessage.error('确认告警失败')
  }
}

// 格式化内存使用率
const formatMemoryUsage = (memory: any) => {
  if (!memory?.total) return '0.0'
  return ((memory.used / memory.total) * 100).toFixed(1)
}

// 格式化内存大小
const formatMemorySize = (bytes: number) => {
  if (!bytes) return '0GB'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)}GB`
}

// 格式化磁盘使用率
const formatDiskUsage = (disk: any) => {
  if (!disk?.total) return '0.0'
  return ((disk.used / disk.total) * 100).toFixed(1)
}

// 格式化磁盘大小
const formatDiskSize = (bytes: number) => {
  if (!bytes) return '0GB'
  const gb = bytes / (1024 * 1024 * 1024)
  return `${gb.toFixed(1)}GB`
}

// 格式化网络速度
const formatNetworkSpeed = (bytesPerSecond: number) => {
  if (!bytesPerSecond) return '0MB/s'
  if (bytesPerSecond >= 1024 * 1024) {
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)}MB/s`
  }
  return `${(bytesPerSecond / 1024).toFixed(1)}KB/s`
}

// 获取服务状态类型
const getServiceStatusType = (status: string) => {
  switch (status) {
    case 'running':
      return 'success'
    case 'stopped':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取告警级别类型
const getAlertLevelType = (level: string) => {
  switch (level) {
    case 'critical':
      return 'danger'
    case 'warning':
      return 'warning'
    default:
      return 'info'
  }
}

// 初始化数据
onMounted(async () => {
  await Promise.all([
    fetchMetrics(),
    fetchServices(),
    fetchAlerts()
  ])
  
  // 定期更新数据
  updateTimer = setInterval(async () => {
    await Promise.all([
      fetchMetrics(),
      fetchServices(),
      fetchAlerts()
    ])
  }, 5000)
})

// 清理定时器
onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style scoped>
.monitor-container {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
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
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.label {
  color: #909399;
  font-size: 14px;
}

.value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.services {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.service-item {
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.service-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.service-name {
  font-weight: bold;
}

.service-meta {
  display: flex;
  justify-content: space-between;
  color: #909399;
  font-size: 14px;
  margin-bottom: 10px;
}

.service-actions {
  display: flex;
  justify-content: flex-end;
}

.alerts {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.alert-item {
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.alert-time {
  color: #909399;
  font-size: 14px;
}

.alert-message {
  margin-bottom: 10px;
  color: #303133;
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
}
</style> 