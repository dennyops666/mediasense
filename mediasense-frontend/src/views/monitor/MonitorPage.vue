<template>
  <div class="monitor-page">
    <div class="overview-section">
      <el-row :gutter="20">
        <!-- ... existing cards ... -->
        
        <el-col :span="6">
          <el-card class="metric-card">
            <template #header>
              <div class="metric-header">
                <el-icon><connection /></el-icon>
                <span>网络 I/O</span>
              </div>
            </template>
            <div class="metric-value network-io">
              <div class="io-item">
                <span class="label">入站：</span>
                <span class="value">{{ formatBytes(monitorStore.metrics?.networkIo.input) }}/s</span>
              </div>
              <div class="io-item">
                <span class="label">出站：</span>
                <span class="value">{{ formatBytes(monitorStore.metrics?.networkIo.output) }}/s</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- ... existing code ... -->
  </div>
</template>

<script setup lang="ts">
// ... existing imports ...
import { Connection } from '@element-plus/icons-vue'

// ... existing code ...

// 格式化字节数
const formatBytes = (bytes: number | undefined) => {
  if (bytes === undefined) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let unitIndex = 0
  
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex++
  }
  
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

// ... existing code ...
</script>

<style scoped>
// ... existing styles ...

.network-io {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.io-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.io-item .label {
  color: var(--el-text-color-secondary);
}

.io-item .value {
  font-weight: bold;
}
</style> 