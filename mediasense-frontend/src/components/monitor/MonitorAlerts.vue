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
                <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
              </div>
            </template>
            
            <div class="alert-details">
              <p class="alert-message">{{ alert.message }}</p>
              <div class="alert-meta">
                <span>来源: {{ alert.source }}</span>
                <span>类型: {{ alert.type }}</span>
              </div>
              <div class="alert-actions">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleAcknowledge(alert.id)"
                  :disabled="alert.acknowledged"
                >
                  {{ alert.acknowledged ? '已确认' : '确认' }}
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

    <!-- 确认对话框 -->
    <el-dialog
      v-model="showConfirm"
      title="确认操作"
      width="30%"
    >
      <span>{{ confirmMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showConfirm = false">取消</el-button>
          <el-button type="primary" @click="handleConfirm">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import type { Alert } from '@/types/monitor'
import { formatDate } from '@/utils/date'
import { ElMessage } from 'element-plus'

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

// 确认对话框
const showConfirm = ref(false)
const confirmMessage = ref('')
const confirmCallback = ref<() => void>()

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
  emit('refresh')
}

const handleAcknowledge = (id: string) => {
  confirmMessage.value = '确认此告警吗？'
  confirmCallback.value = () => {
    emit('acknowledge', id)
    showConfirm.value = false
  }
  showConfirm.value = true
}

const handleDelete = (id: string) => {
  confirmMessage.value = '确定删除此告警吗？'
  confirmCallback.value = () => {
    emit('delete', id)
    showConfirm.value = false
  }
  showConfirm.value = true
}

const handleClearAll = () => {
  confirmMessage.value = '确定清除所有告警吗？'
  confirmCallback.value = () => {
    emit('clear-all')
    showConfirm.value = false
  }
  showConfirm.value = true
}

const handleConfirm = () => {
  if (confirmCallback.value) {
    confirmCallback.value()
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

.alert-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
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