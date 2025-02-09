<template>
  <div class="monitor-alerts">
    <div class="alerts-header">
      <h3>系统告警</h3>
      <div class="alerts-actions">
        <el-button
          type="primary"
          size="small"
          @click="handleRefresh"
          :loading="loading"
        >
          刷新
        </el-button>
        <el-button
          type="success"
          size="small"
          @click="handleClearAll"
          :disabled="!alerts.length"
        >
          清除全部
        </el-button>
        <el-button
          type="info"
          size="small"
          @click="showHistory = true"
        >
          历史记录
        </el-button>
      </div>
    </div>

    <div class="alerts-content">
      <el-empty
        v-if="!alerts.length"
        description="暂无告警信息"
      />
      
      <template v-else>
        <el-collapse v-model="activeAlerts">
          <el-collapse-item
            v-for="alert in alerts"
            :key="alert.id"
            :name="alert.id"
            :class="['alert-item', `alert-item--${alert.level}`]"
          >
            <template #title>
              <div class="alert-header">
                <el-tag :type="getAlertLevelType(alert.level)" size="small">
                  {{ alert.level }}
                </el-tag>
                <span class="alert-source">{{ alert.source }}</span>
                <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
              </div>
            </template>
            
            <div class="alert-details">
              <p class="alert-message">{{ alert.message }}</p>
              <div class="alert-actions">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleAcknowledge(alert.id)"
                >
                  确认
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(alert.id)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="alerts-pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </template>
    </div>

    <!-- 历史记录对话框 -->
    <el-dialog
      v-model="showHistory"
      title="告警历史"
      width="70%"
    >
      <el-table :data="store.alertHistory" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getAlertLevelType(row.level)">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="message" label="消息" />
        <el-table-column label="确认信息" width="200">
          <template #default="{ row }">
            <template v-if="row.acknowledged">
              {{ formatDate(row.acknowledged.time) }}
              <br>
              <small>by {{ row.acknowledged.by }}</small>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import type { Alert } from '@/types/monitor'
import { formatDate } from '@/utils/date'
import { ElMessageBox } from 'element-plus'

const props = defineProps<{
  alerts: Alert[]
  loading: boolean
  total: number
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'acknowledge', id: string): void
  (e: 'delete', id: string): void
  (e: 'clear-all'): void
  (e: 'page-change', page: number): void
  (e: 'size-change', size: number): void
}>()

const store = useMonitorStore()
const activeAlerts = ref<string[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const showHistory = ref(false)

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

// 事件处理
const handleRefresh = () => {
  store.fetchAlerts()
}

const handleAcknowledge = async (id: string) => {
  try {
    const username = 'admin' // TODO: 从用户状态获取
    await store.acknowledgeAlert(id, username)
  } catch (error) {
    ElMessageBox.alert('确认告警失败', '错误', { type: 'error' })
  }
}

const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除此告警吗？', '提示', {
      type: 'warning'
    })
    const username = 'admin' // TODO: 从用户状态获取
    await store.acknowledgeAlert(id, username)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessageBox.alert('删除告警失败', '错误', { type: 'error' })
    }
  }
}

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm('确定清除所有告警吗？', '提示', {
      type: 'warning'
    })
    const username = 'admin' // TODO: 从用户状态获取
    await store.clearAllAlerts(username)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessageBox.alert('清除告警失败', '错误', { type: 'error' })
    }
  }
}

const handleSizeChange = (size: number) => {
  emit('size-change', size)
}

const handleCurrentChange = (page: number) => {
  emit('page-change', page)
}
</script>

<style scoped>
.monitor-alerts {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.alerts-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.alerts-actions {
  display: flex;
  gap: 8px;
}

.alerts-content {
  flex: 1;
  overflow-y: auto;
}

.alert-item {
  margin-bottom: 8px;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-source {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.alert-time {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.alert-details {
  padding: 16px;
}

.alert-message {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.alerts-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.alert-item--critical {
  border-left: 4px solid var(--el-color-danger);
}

.alert-item--warning {
  border-left: 4px solid var(--el-color-warning);
}

.alert-item--info {
  border-left: 4px solid var(--el-color-info);
}
</style> 