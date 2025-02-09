<template>
  <div class="alerts">
    <!-- 告警统计 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="(stat, index) in alertStats" :key="index">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-icon" :style="{ backgroundColor: stat.bgColor }">
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

    <!-- 告警列表 -->
    <el-card class="alert-list">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">告警列表</span>
            <el-radio-group v-model="alertStatus" size="small">
              <el-radio-button label="active">活跃告警</el-radio-button>
              <el-radio-button label="history">历史记录</el-radio-button>
            </el-radio-group>
          </div>
          <div class="header-right">
            <el-button type="primary" @click="exportAlerts">
              导出记录
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filterForm.timeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              :shortcuts="dateShortcuts"
            />
          </el-form-item>
          <el-form-item label="告警级别">
            <el-select v-model="filterForm.level" clearable placeholder="全部">
              <el-option label="严重" value="critical" />
              <el-option label="警告" value="warning" />
              <el-option label="一般" value="info" />
            </el-select>
          </el-form-item>
          <el-form-item label="告警源">
            <el-select v-model="filterForm.source" clearable placeholder="全部">
              <el-option
                v-for="source in alertSources"
                :key="source"
                :label="source"
                :value="source"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 告警表格 -->
      <el-table
        :data="alertList"
        style="width: 100%"
        :default-sort="{ prop: 'timestamp', order: 'descending' }"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="alert-detail">
              <div class="detail-item">
                <span class="label">告警ID:</span>
                <span class="value">{{ row.id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">详细信息:</span>
                <span class="value">{{ row.detail }}</span>
              </div>
              <div class="detail-item">
                <span class="label">建议操作:</span>
                <span class="value">{{ row.suggestion }}</span>
              </div>
              <div v-if="row.acknowledged" class="detail-item">
                <span class="label">处理人:</span>
                <span class="value">{{ row.acknowledged.by }}</span>
              </div>
              <div v-if="row.acknowledged" class="detail-item">
                <span class="label">处理时间:</span>
                <span class="value">{{ formatDate(row.acknowledged.time) }}</span>
              </div>
              <div v-if="row.acknowledged" class="detail-item">
                <span class="label">处理备注:</span>
                <span class="value">{{ row.acknowledged.comment }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
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
        <el-table-column prop="source" label="来源" width="150" />
        <el-table-column prop="message" label="告警信息" min-width="300" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.acknowledged ? 'success' : 'warning'">
              {{ row.acknowledged ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.acknowledged"
              type="primary"
              link
              @click="handleAcknowledge(row)"
            >
              处理
            </el-button>
            <el-button
              type="danger"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalAlerts"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </el-card>

    <!-- 处理告警对话框 -->
    <el-dialog
      v-model="acknowledgeDialog.visible"
      title="处理告警"
      width="500px"
    >
      <el-form
        ref="acknowledgeFormRef"
        :model="acknowledgeDialog.form"
        :rules="acknowledgeDialog.rules"
        label-width="100px"
      >
        <el-form-item label="处理人" prop="by">
          <el-input v-model="acknowledgeDialog.form.by" />
        </el-form-item>
        <el-form-item label="处理备注" prop="comment">
          <el-input
            v-model="acknowledgeDialog.form.comment"
            type="textarea"
            :rows="4"
            placeholder="请输入处理的具体情况和解决方案"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="acknowledgeDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitAcknowledge">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Warning,
  Bell,
  Timer,
  Document
} from '@element-plus/icons-vue'

// 告警统计
const alertStats = [
  {
    label: '严重告警',
    value: '3',
    icon: Warning,
    color: '#fff',
    bgColor: '#F56C6C'
  },
  {
    label: '警告告警',
    value: '5',
    icon: Bell,
    color: '#fff',
    bgColor: '#E6A23C'
  },
  {
    label: '今日告警',
    value: '12',
    icon: Timer,
    color: '#fff',
    bgColor: '#409EFF'
  },
  {
    label: '历史记录',
    value: '128',
    icon: Document,
    color: '#fff',
    bgColor: '#909399'
  }
]

// 状态变量
const alertStatus = ref('active')
const currentPage = ref(1)
const pageSize = ref(20)
const totalAlerts = ref(150)
const alertSources = ['Server-01', 'Server-02', 'Server-03', 'Database', 'Network']

// 筛选表单
const filterForm = ref({
  timeRange: null,
  level: '',
  source: ''
})

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000)
      return [start, end]
    }
  },
  {
    text: '今天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setHours(0, 0, 0, 0)
      return [start, end]
    }
  },
  {
    text: '最近三天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 3)
      return [start, end]
    }
  },
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  }
]

// 告警列表数据
const alertList = ref([
  {
    id: 'ALT001',
    timestamp: new Date().getTime() - 1000 * 60 * 30,
    level: '严重',
    source: 'Server-01',
    message: 'CPU使用率超过90%',
    detail: 'CPU使用率持续5分钟超过90%，可能导致系统响应缓慢',
    suggestion: '检查是否有异常进程占用过多CPU资源，必要时进行处理',
    acknowledged: null
  },
  {
    id: 'ALT002',
    timestamp: new Date().getTime() - 1000 * 60 * 45,
    level: '警告',
    source: 'Database',
    message: '数据库连接数接近上限',
    detail: '当前连接数已达到最大连接数的85%',
    suggestion: '检查是否存在连接泄露，考虑增加最大连接数限制',
    acknowledged: {
      time: new Date().getTime() - 1000 * 60 * 15,
      by: '张工',
      comment: '已清理无用连接，并增加了最大连接数限制'
    }
  }
])

// 处理告警对话框
const acknowledgeDialog = ref({
  visible: false,
  currentAlert: null,
  form: {
    by: '',
    comment: ''
  },
  rules: {
    by: [
      { required: true, message: '请输入处理人', trigger: 'blur' }
    ],
    comment: [
      { required: true, message: '请输入处理备注', trigger: 'blur' }
    ]
  }
})

// 格式化函数
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const getAlertLevelType = (level: string) => {
  const map: Record<string, string> = {
    '严重': 'danger',
    '警告': 'warning',
    '一般': 'info'
  }
  return map[level] || 'info'
}

// 事件处理函数
const handleFilter = () => {
  // TODO: 实现筛选逻辑
  console.log('Filter form:', filterForm.value)
}

const resetFilter = () => {
  filterForm.value = {
    timeRange: null,
    level: '',
    source: ''
  }
}

const handleAcknowledge = (alert: any) => {
  acknowledgeDialog.value.currentAlert = alert
  acknowledgeDialog.value.visible = true
}

const submitAcknowledge = () => {
  // TODO: 实现提交处理逻辑
  const alert = acknowledgeDialog.value.currentAlert
  const form = acknowledgeDialog.value.form
  
  if (alert) {
    alert.acknowledged = {
      time: new Date().getTime(),
      by: form.by,
      comment: form.comment
    }
  }
  
  ElMessage.success('告警已处理')
  acknowledgeDialog.value.visible = false
  acknowledgeDialog.value.form = {
    by: '',
    comment: ''
  }
}

const handleDelete = async (alert: any) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除该告警记录吗？此操作不可恢复',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    // TODO: 实现删除逻辑
    const index = alertList.value.indexOf(alert)
    if (index > -1) {
      alertList.value.splice(index, 1)
    }
    ElMessage.success('告警记录已删除')
  } catch {
    // 用户取消操作
  }
}

const exportAlerts = () => {
  // TODO: 实现导出逻辑
  ElMessage.success('告警记录导出成功')
}
</script>

<style scoped>
.alerts {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-icon {
  padding: 20px;
  border-radius: 8px;
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

.alert-list {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  font-size: 16px;
  font-weight: bold;
}

.filter-bar {
  margin-bottom: 20px;
  padding: 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.alert-detail {
  padding: 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.detail-item {
  margin-bottom: 10px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.detail-item .label {
  width: 80px;
  color: var(--el-text-color-secondary);
}

.detail-item .value {
  flex: 1;
  color: var(--el-text-color-primary);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-card__header) {
  padding: 15px 20px;
}
</style> 