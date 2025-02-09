<template>
  <el-card class="batch-progress">
    <template #header>
      <div class="card-header">
        <span class="progress-status">{{ statusText }}</span>
        <el-button v-if="status === 'running'" type="danger" @click="handleStop">停止</el-button>
      </div>
    </template>

    <div class="progress-section">
      <el-progress
        :percentage="progress"
        :status="progressStatus"
        :stroke-width="20"
      >
        <template #default="{ percentage }">
          <span class="progress-label">{{ percentage }}%</span>
        </template>
      </el-progress>

      <div class="statistics">
        <div class="stat-item">
          <span class="stat-label">总任务数</span>
          <span class="stat-value">{{ total }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已完成</span>
          <span class="stat-value">{{ completed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">失败</span>
          <span class="stat-value">{{ failed }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">预计剩余时间</span>
          <span class="stat-value">{{ remainingTimeText }}</span>
        </div>
      </div>
    </div>

    <el-collapse v-if="showDetails">
      <el-collapse-item title="详细信息">
        <el-table :data="details" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="任务名称" />
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" />
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script lang="ts">
import { computed, defineComponent } from 'vue'
import { ElMessageBox } from 'element-plus'

export default defineComponent({
  name: 'AIBatchProgress',
  props: {
    progress: {
      type: Number,
      default: 0
    },
    status: {
      type: String,
      default: 'pending'
    },
    total: {
      type: Number,
      default: 0
    },
    completed: {
      type: Number,
      default: 0
    },
    failed: {
      type: Number,
      default: 0
    },
    estimatedTime: {
      type: Number,
      default: 0
    },
    showDetails: {
      type: Boolean,
      default: false
    },
    details: {
      type: Array,
      default: () => []
    }
  },

  setup(props, { emit }) {
    const statusText = computed(() => {
      switch (props.status) {
        case 'running':
          return '处理中'
        case 'completed':
          return '已完成'
        case 'failed':
          return '失败'
        case 'pending':
          return '等待中'
        default:
          return '未知状态'
      }
    })

    const progressStatus = computed(() => {
      switch (props.status) {
        case 'completed':
          return 'success'
        case 'failed':
          return 'exception'
        default:
          return ''
      }
    })

    const remainingTimeText = computed(() => {
      if (props.status !== 'running' || props.estimatedTime <= 0) {
        return '--'
      }
      const minutes = Math.floor(props.estimatedTime / 60)
      const seconds = props.estimatedTime % 60
      return `${minutes}分${seconds}秒`
    })

    const handleStop = async () => {
      try {
        await ElMessageBox.confirm('确定要停止当前批处理任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        emit('stop')
      } catch (error) {
        // 用户取消操作，不做任何处理
      }
    }

    const getStatusType = (status: string) => {
      switch (status) {
        case 'completed':
          return 'success'
        case 'running':
          return 'primary'
        case 'failed':
          return 'danger'
        default:
          return 'info'
      }
    }

    const getStatusText = (status: string) => {
      switch (status) {
        case 'completed':
          return '已完成'
        case 'running':
          return '处理中'
        case 'failed':
          return '失败'
        case 'pending':
          return '等待中'
        default:
          return '未知状态'
      }
    }

    return {
      statusText,
      progressStatus,
      remainingTimeText,
      handleStop,
      getStatusType,
      getStatusText
    }
  }
})
</script>

<style scoped>
.batch-progress {
  margin: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-section {
  margin: 20px 0;
}

.statistics {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: #909399;
  font-size: 14px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
  margin-top: 5px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
}

.progress-status {
  font-size: 16px;
  font-weight: bold;
}
</style>
