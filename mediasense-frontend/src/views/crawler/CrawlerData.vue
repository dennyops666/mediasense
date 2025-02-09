<template>
  <div class="crawler-data">
    <!-- 顶部操作栏 -->
    <div class="operation-bar">
      <div class="left-actions">
        <el-select v-model="taskId" placeholder="选择爬虫任务" @change="handleTaskChange">
          <el-option
            v-for="task in tasks"
            :key="task.id"
            :label="task.name"
            :value="task.id"
          />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          @change="handleDateChange"
        />

        <el-input
          v-model="searchKeyword"
          placeholder="搜索关键词"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="right-actions">
        <el-button-group>
          <el-button type="primary" @click="handleExport">
            <el-icon><Download /></el-icon>导出数据
          </el-button>
          <el-button type="danger" @click="handleBatchDelete" :disabled="!selectedData.length">
            <el-icon><Delete /></el-icon>批量删除
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="dataList"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="data-detail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="URL">
                <el-link :href="row.url" target="_blank" type="primary">
                  {{ row.url }}
                </el-link>
              </el-descriptions-item>
              <el-descriptions-item label="采集时间">
                {{ formatDate(row.crawlTime) }}
              </el-descriptions-item>
              <el-descriptions-item label="原始数据" :span="2">
                <pre class="json-content">{{ JSON.stringify(row.rawData, null, 2) }}</pre>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
      <el-table-column prop="source" label="来源" width="150" />
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="publishTime" label="发布时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.publishTime) }}
        </template>
      </el-table-column>
      <el-table-column prop="crawlTime" label="采集时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.crawlTime) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button type="primary" link @click="handleView(row)">
              <el-icon><View /></el-icon>查看
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
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

    <!-- 数据详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="数据详情"
      width="80%"
      class="data-dialog"
    >
      <template v-if="currentData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">
            {{ currentData.title }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            {{ currentData.source }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag>{{ currentData.category }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="URL" :span="2">
            <el-link :href="currentData.url" target="_blank" type="primary">
              {{ currentData.url }}
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ formatDate(currentData.publishTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="采集时间">
            {{ formatDate(currentData.crawlTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="内容" :span="2">
            <div class="content-preview" v-html="currentData.content"></div>
          </el-descriptions-item>
          <el-descriptions-item label="原始数据" :span="2">
            <pre class="json-content">{{ JSON.stringify(currentData.rawData, null, 2) }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Download,
  Delete,
  View
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import { useCrawlerStore } from '@/stores/crawler'
import type { CrawlerTask, CrawlerData } from '@/types/crawler'

const store = useCrawlerStore()

// 状态变量
const loading = ref(false)
const taskId = ref('')
const tasks = ref<CrawlerTask[]>([])
const dateRange = ref<[Date, Date] | null>(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedData = ref<CrawlerData[]>([])
const dataList = ref<CrawlerData[]>([])
const detailVisible = ref(false)
const currentData = ref<CrawlerData | null>(null)

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    }
  }
]

// 获取任务列表
const fetchTasks = async () => {
  try {
    const { data } = await store.fetchTasks()
    tasks.value = data
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  }
}

// 获取数据列表
const fetchDataList = async () => {
  loading.value = true
  try {
    const params = {
      taskId: taskId.value,
      startTime: dateRange.value?.[0]?.toISOString(),
      endTime: dateRange.value?.[1]?.toISOString(),
      keyword: searchKeyword.value,
      page: currentPage.value,
      pageSize: pageSize.value
    }
    const { data, total: totalCount } = await store.fetchCrawlerData(params)
    dataList.value = data
    total.value = totalCount
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 事件处理
const handleTaskChange = () => {
  currentPage.value = 1
  fetchDataList()
}

const handleDateChange = () => {
  currentPage.value = 1
  fetchDataList()
}

const handleSearch = () => {
  currentPage.value = 1
  fetchDataList()
}

const handleView = (row: CrawlerData) => {
  currentData.value = row
  detailVisible.value = true
}

const handleDelete = async (row: CrawlerData) => {
  try {
    await ElMessageBox.confirm('确定要删除该数据吗？', '警告', {
      type: 'warning'
    })
    await store.deleteCrawlerData(row.id)
    ElMessage.success('数据已删除')
    fetchDataList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedData.value.length} 条数据吗？`,
      '警告',
      {
        type: 'warning'
      }
    )
    const ids = selectedData.value.map(item => item.id)
    await store.batchDeleteCrawlerData(ids)
    ElMessage.success('数据已删除')
    fetchDataList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    const params = {
      taskId: taskId.value,
      startTime: dateRange.value?.[0]?.toISOString(),
      endTime: dateRange.value?.[1]?.toISOString(),
      keyword: searchKeyword.value
    }
    await store.exportCrawlerData(params)
    ElMessage.success('数据导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleSelectionChange = (selection: CrawlerData[]) => {
  selectedData.value = selection
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchDataList()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchDataList()
}

// 初始化
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.crawler-data {
  padding: 20px;
}

.operation-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-actions {
  display: flex;
  gap: 16px;
}

.data-detail {
  padding: 20px;
}

.json-content {
  background-color: var(--el-fill-color-light);
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.content-preview {
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-descriptions) {
  margin-bottom: 20px;
}

:deep(.el-descriptions__label) {
  width: 120px;
}
</style> 