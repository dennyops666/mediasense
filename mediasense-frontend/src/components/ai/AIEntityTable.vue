<template>
  <div class="ai-entity-table">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>实体识别结果</span>
          <div class="header-actions">
            <el-button 
              type="primary" 
              size="small"
              :disabled="!hasData"
              @click="handleExport"
            >
              导出
            </el-button>
            <el-button 
              type="info" 
              size="small"
              :loading="loading"
              @click="handleRefresh"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div class="table-container" v-loading="loading">
        <div class="table-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索实体"
            clearable
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select
            v-model="selectedTypes"
            multiple
            collapse-tags
            placeholder="实体类型"
            class="type-filter"
          >
            <el-option
              v-for="type in entityTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>

          <el-select
            v-model="sortBy"
            placeholder="排序方式"
            class="sort-select"
          >
            <el-option label="频次 (高到低)" value="frequency-desc" />
            <el-option label="频次 (低到高)" value="frequency-asc" />
            <el-option label="首次出现时间" value="first-occurrence" />
            <el-option label="最近出现时间" value="last-occurrence" />
          </el-select>
        </div>

        <el-table
          :data="filteredEntities"
          style="width: 100%"
          :max-height="tableMaxHeight"
          border
        >
          <el-table-column prop="name" label="实体名称" min-width="150">
            <template #default="{ row }">
              <div class="entity-name">
                <span>{{ row.name }}</span>
                <el-tag size="small" :type="getTypeTagType(row.type)">
                  {{ row.type }}
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="frequency" label="出现频次" width="100" sortable>
            <template #default="{ row }">
              <el-badge :value="row.frequency" type="primary" />
            </template>
          </el-table-column>

          <el-table-column prop="confidence" label="置信度" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.round(row.confidence * 100)"
                :status="getConfidenceStatus(row.confidence)"
              />
            </template>
          </el-table-column>

          <el-table-column prop="firstOccurrence" label="首次出现" width="180">
            <template #default="{ row }">
              {{ formatDate(row.firstOccurrence) }}
            </template>
          </el-table-column>

          <el-table-column prop="lastOccurrence" label="最近出现" width="180">
            <template #default="{ row }">
              {{ formatDate(row.lastOccurrence) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button 
                text 
                type="primary"
                @click="handleViewDetails(row)"
              >
                详情
              </el-button>
              <el-button 
                text 
                type="danger"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-footer">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="totalItems"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="detailsVisible"
      title="实体详情"
      width="60%"
      destroy-on-close
    >
      <entity-details
        v-if="detailsVisible"
        :entity="selectedEntity"
        @close="detailsVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { Entity } from '@/types/ai'

// 组件属性
interface Props {
  entities: Entity[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  entities: () => [],
  loading: false
})

// 组件事件
const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'delete', entity: Entity): void
  (e: 'export'): void
}>()

// 状态
const searchKeyword = ref('')
const selectedTypes = ref<string[]>([])
const sortBy = ref('frequency-desc')
const currentPage = ref(1)
const pageSize = ref(20)
const detailsVisible = ref(false)
const selectedEntity = ref<Entity | null>(null)
const tableMaxHeight = ref(500)

// 实体类型选项
const entityTypes = [
  { label: '人物', value: 'PERSON' },
  { label: '组织', value: 'ORGANIZATION' },
  { label: '地点', value: 'LOCATION' },
  { label: '时间', value: 'TIME' },
  { label: '事件', value: 'EVENT' },
  { label: '产品', value: 'PRODUCT' },
  { label: '其他', value: 'OTHER' }
]

// 计算属性
const hasData = computed(() => props.entities.length > 0)

const filteredEntities = computed(() => {
  let result = [...props.entities]

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(entity => 
      entity.name.toLowerCase().includes(keyword)
    )
  }

  // 类型筛选
  if (selectedTypes.value.length > 0) {
    result = result.filter(entity =>
      selectedTypes.value.includes(entity.type)
    )
  }

  // 排序
  result.sort((a, b) => {
    switch (sortBy.value) {
      case 'frequency-desc':
        return b.frequency - a.frequency
      case 'frequency-asc':
        return a.frequency - b.frequency
      case 'first-occurrence':
        return new Date(a.firstOccurrence).getTime() - new Date(b.firstOccurrence).getTime()
      case 'last-occurrence':
        return new Date(b.lastOccurrence).getTime() - new Date(a.lastOccurrence).getTime()
      default:
        return 0
    }
  })

  return result.slice(
    (currentPage.value - 1) * pageSize.value,
    currentPage.value * pageSize.value
  )
})

const totalItems = computed(() => {
  let result = props.entities
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(entity => 
      entity.name.toLowerCase().includes(keyword)
    )
  }

  if (selectedTypes.value.length > 0) {
    result = result.filter(entity =>
      selectedTypes.value.includes(entity.type)
    )
  }

  return result.length
})

// 方法
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    PERSON: '',
    ORGANIZATION: 'success',
    LOCATION: 'warning',
    TIME: 'info',
    EVENT: 'danger',
    PRODUCT: 'primary',
    OTHER: 'info'
  }
  return typeMap[type] || 'info'
}

const getConfidenceStatus = (confidence: number) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'exception'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

const handleRefresh = () => {
  emit('refresh')
}

const handleExport = () => {
  emit('export')
}

const handleDelete = async (entity: Entity) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除实体"${entity.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', entity)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消操作
  }
}

const handleViewDetails = (entity: Entity) => {
  selectedEntity.value = entity
  detailsVisible.value = true
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}
</script>

<style scoped>
.ai-entity-table {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.table-container {
  margin-top: 20px;
}

.table-toolbar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.search-input {
  width: 200px;
}

.type-filter {
  width: 200px;
}

.sort-select {
  width: 150px;
}

.entity-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
