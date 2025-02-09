<template>
  <div class="monitor-dashboard" data-test="monitor-dashboard">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="metric-card" data-test="cpu-metric">
          <template #header>CPU 使用情况</template>
          <el-progress 
            :percentage="store.metrics?.cpu?.usage || 0"
            :status="store.metrics?.cpu?.usage > 80 ? 'exception' : 'normal'"
            :format="(percentage) => `${percentage}%`"
          />
          <div class="metric-details">
            <span>{{ store.metrics?.cpu?.cores }} 核</span>
            <span>{{ store.metrics?.cpu?.temperature }}°C</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="metric-card" data-test="memory-metric">
          <template #header>内存使用情况</template>
          <el-progress 
            :percentage="store.metrics?.memory?.usagePercentage || 0"
            :status="store.metrics?.memory?.usagePercentage > 80 ? 'exception' : 'normal'"
            :format="(percentage) => `${percentage}%`"
          />
          <div class="metric-details">
            <span>总内存：{{ store.metrics?.memory?.total }}</span>
            <span>已使用：{{ store.metrics?.memory?.used }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="metric-card" data-test="disk-metric">
          <template #header>磁盘使用情况</template>
          <el-progress 
            :percentage="store.metrics?.disk?.usagePercentage || 0"
            :status="store.metrics?.disk?.usagePercentage > 90 ? 'exception' : 'normal'"
            :format="(percentage) => `${percentage}%`"
          />
          <div class="metric-details">
            <span>总容量：{{ store.metrics?.disk?.total }}</span>
            <span>已使用：{{ store.metrics?.disk?.used }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="metric-card" data-test="network-metric">
          <template #header>网络状态</template>
          <div class="metric-details">
            <div>网络延迟: {{ store.metrics?.network?.latency }}ms</div>
            <div>上传：{{ store.metrics?.network?.upload }}</div>
            <div>下载：{{ store.metrics?.network?.download }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-4">
      <el-col :span="24">
        <el-card data-test="alerts-card">
          <template #header>
            <div class="alert-header">
              <span>告警列表</span>
              <el-button
                type="primary"
                size="small"
                data-test="clear-alerts-btn"
                @click="handleClearAlerts"
              >
                清空告警历史
              </el-button>
            </div>
          </template>
          <div v-if="store.alerts.length > 0">
            <div
              v-for="alert in store.alerts"
              :key="alert.id"
              class="alert-item"
              data-test="alert-item"
            >
              <el-alert
                :title="alert.message"
                :type="alert.level === 'error' ? 'error' : 'warning'"
                :description="alert.timestamp"
                show-icon
                :closable="true"
                @close="handleAcknowledgeAlert(alert.id)"
              />
            </div>
          </div>
          <el-empty v-else description="暂无告警" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-4">
      <el-col :span="24">
        <el-card>
          <template #header>监控设置</template>
          <div class="monitor-settings">
            <div class="setting-item">
              <span>监控状态：</span>
              <el-tag
                data-test="monitor-status"
                :type="store.isMonitoring ? 'success' : 'info'"
              >
                {{ store.isMonitoring ? '监控中' : '已停止' }}
              </el-tag>
            </div>
            <div class="setting-item">
              <span>监控间隔：</span>
              <el-select
                v-model="monitoringInterval"
                data-test="monitor-interval"
                @change="handleIntervalChange"
              >
                <el-option :value="1000" label="1 秒" />
                <el-option :value="5000" label="5 秒" />
                <el-option :value="10000" label="10 秒" />
                <el-option :value="60000" label="1 分钟" />
              </el-select>
            </div>
            <div class="setting-item">
              <el-button
                type="primary"
                data-test="export-btn"
                :loading="isExporting"
                @click="handleExport"
              >
                导出监控数据
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-alert
      v-if="store.errorMessage"
      data-test="error-message"
      :title="store.errorMessage"
      type="error"
      show-icon
      class="mt-4"
    >
      <template #default>
        <el-button
          type="primary"
          size="small"
          data-test="retry-btn"
          @click="handleRetry"
        >
          重试
        </el-button>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'

const store = useMonitorStore()
const monitoringInterval = ref(5000)
const isExporting = ref(false)

onMounted(async () => {
  await store.startMonitoring(monitoringInterval.value)
})

onUnmounted(() => {
  store.stopMonitoring()
})

const handleIntervalChange = async (value) => {
  try {
    await store.stopMonitoring()
    await store.startMonitoring(value)
    ElMessage.success('监控间隔已更新')
  } catch (error) {
    ElMessage.error('更新监控间隔失败')
  }
}

const handleAcknowledgeAlert = async (alertId) => {
  try {
    await store.acknowledgeAlert(alertId)
    ElMessage.success('告警已确认')
  } catch (error) {
    ElMessage.error('确认告警失败')
  }
}

const handleClearAlerts = async () => {
  try {
    await store.clearAllAlerts()
    ElMessage.success('告警历史已清空')
  } catch (error) {
    ElMessage.error('清空告警历史失败')
  }
}

const handleExport = async () => {
  try {
    isExporting.value = true
    await store.exportMonitoringData()
    ElMessage.success('监控数据已导出')
  } catch (error) {
    ElMessage.error('导出监控数据失败')
  } finally {
    isExporting.value = false
  }
}

const handleRetry = async () => {
  try {
    await store.startMonitoring(monitoringInterval.value)
  } catch (error) {
    ElMessage.error('重试失败')
  }
}
</script>

<style scoped>
.monitor-dashboard {
  padding: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.metric-card {
  margin-bottom: 20px;
}

.metric-details {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-item {
  margin-bottom: 8px;
}

.monitor-settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>