<template>
  <div class="crawler-data-list">
    <div class="header">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索数据"
        @input="handleSearch"
        data-test="search-input"
      />
      <el-button type="primary" @click="handleExport" data-test="export-button">
        导出数据
      </el-button>
    </div>

    <div v-if="error" class="error-message" data-test="error-message">
      {{ error }}
    </div>

    <el-table
      v-loading="loading"
      :data="filteredData"
      style="width: 100%"
      data-test="data-table"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="url" label="URL" show-overflow-tooltip />
      <el-table-column prop="createdAt" label="采集时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button
            type="text"
            @click="handleView(row)"
            data-test="view-button"
          >
            查看
          </el-button>
          <el-button
            type="text"
            @click="handleDelete(row)"
            data-test="delete-button"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      data-test="pagination"
    />

    <el-dialog
      v-model="dialogVisible"
      title="数据详情"
      width="60%"
      data-test="detail-dialog"
    >
      <pre>{{ JSON.stringify(currentData, null, 2) }}</pre>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCrawlerStore } from '@/stores/crawler'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true,
    validator: (value) => {
      return typeof value === 'string' || typeof value === 'number'
    }
  }
})

const store = useCrawlerStore()

const loading = ref(false)
const error = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const currentData = ref(null)

const total = computed(() => store.data.length)

const filteredData = computed(() => {
  let result = store.data
  if (searchKeyword.value) {
    result = result.filter(item => 
      item.title.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      item.url.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }
  const start = (currentPage.value - 1) * pageSize.value
  return result.slice(start, start + pageSize.value)
})

onMounted(async () => {
  try {
    loading.value = true
    error.value = ''
    await store.fetchData({
      taskId: props.taskId,
      page: currentPage.value,
      pageSize: pageSize.value
    })
  } catch (err) {
    error.value = '获取数据失败'
    console.error('获取数据失败:', err)
  } finally {
    loading.value = false
  }
})

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = async (val: number) => {
  try {
    loading.value = true
    error.value = ''
    pageSize.value = val
    currentPage.value = 1
    await store.fetchData({
      taskId: props.taskId,
      page: currentPage.value,
      pageSize: pageSize.value
    })
  } catch (err) {
    error.value = '获取数据失败'
    console.error('获取数据失败:', err)
  } finally {
    loading.value = false
  }
}

const handleCurrentChange = async (val: number) => {
  try {
    loading.value = true
    error.value = ''
    currentPage.value = val
    await store.fetchData({
      taskId: props.taskId,
      page: currentPage.value,
      pageSize: pageSize.value
    })
  } catch (err) {
    error.value = '获取数据失败'
    console.error('获取数据失败:', err)
  } finally {
    loading.value = false
  }
}

const handleView = (row: any) => {
  currentData.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    loading.value = true
    error.value = ''
    await store.deleteData(row.id)
    ElMessage.success('删除成功')
  } catch (err) {
    if (err !== 'cancel') {
      error.value = '删除数据失败'
      console.error('删除数据失败:', err)
      ElMessage.error('删除失败')
    }
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  try {
    loading.value = true
    error.value = ''
    await store.exportData({
      taskId: props.taskId
    })
    ElMessage.success('导出成功')
  } catch (err) {
    error.value = '导出数据失败'
    console.error('导出数据失败:', err)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.crawler-data-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header .el-input {
  width: 300px;
}

.error-message {
  color: #f56c6c;
  margin: 10px 0;
  padding: 8px 16px;
  background-color: #fef0f0;
  border-radius: 4px;
}
</style> 