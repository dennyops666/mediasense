<template>
  <div class="search-page">
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="search-form">
      <el-input
        v-model="keyword"
        placeholder="请输入搜索关键词"
        class="search-input"
        @input="handleInput"
      />
      
      <el-select
        v-model="type"
        placeholder="选择类型"
        class="type-select"
        @change="handleSearch"
      >
        <el-option label="全部" value="" />
        <el-option label="新闻" value="news" />
        <el-option label="社交媒体" value="social" />
      </el-select>

      <el-date-picker
        v-model="date"
        type="date"
        placeholder="选择日期"
        class="date-picker"
        @change="handleSearch"
      />

      <el-button
        type="primary"
        :loading="loading"
        @click="handleSearch"
      >
        搜索
      </el-button>
    </div>

    <div v-if="suggestions.length" class="search-suggestions">
      <div
        v-for="suggestion in suggestions"
        :key="suggestion"
        class="suggestion-item"
        @click="handleSelectSuggestion(suggestion)"
      >
        {{ suggestion }}
      </div>
    </div>

    <div v-if="searchHistory.length" class="search-history">
      <div class="history-header">
        <h3>搜索历史</h3>
        <el-button
          type="text"
          class="clear-history"
          @click="handleClearHistory"
        >
          清空历史
        </el-button>
      </div>
      <div class="history-list">
        <div
          v-for="item in searchHistory"
          :key="item"
          class="history-item"
          @click="handleSelectHistory(item)"
        >
          {{ item }}
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading" loading="true">
      <el-loading />
    </div>

    <div v-else-if="results.length" class="search-results">
      <div class="search-stats">
        共找到 {{ total }} 条结果
      </div>

      <div
        v-for="item in results"
        :key="item.id"
        class="search-result-item"
        @click="handleViewDetail(item.id)"
      >
        <h3>{{ item.title }}</h3>
        <p>{{ item.content }}</p>
        <div class="item-meta">
          <span>{{ item.source }}</span>
          <span>{{ item.publishTime }}</span>
          <span class="relevance-score">相关度: {{ item.relevanceScore.toFixed(2) }}</span>
        </div>
      </div>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-else-if="!loading" class="no-results">
      暂无搜索结果
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useSearchStore } from '@/stores/search'
import type { SearchResult } from '@/types/search'

const store = useSearchStore()
const loading = ref(false)
const error = ref<string | null>(null)
const keyword = ref('')
const type = ref('')
const date = ref<string | null>(null)
const results = ref<SearchResult[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const suggestions = ref<string[]>([])
const searchHistory = ref<string[]>([])

const emit = defineEmits<{
  (e: 'view-detail', id: string): void
}>()

onMounted(() => {
  loadSearchHistory()
})

const loadSearchHistory = () => {
  const history = localStorage.getItem('searchHistory')
  if (history) {
    searchHistory.value = JSON.parse(history)
  }
}

const saveSearchHistory = () => {
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
}

const handleInput = async (value: string) => {
  if (!value) {
    suggestions.value = []
    return
  }

  try {
    suggestions.value = await store.getSuggestions(value)
  } catch (err) {
    console.error('获取搜索建议失败:', err)
  }
}

const handleSearch = async () => {
  try {
    loading.value = true
    error.value = null
    suggestions.value = []

    const response = await store.search({
      keyword: keyword.value,
      type: type.value || undefined,
      date: date.value || undefined,
      page: currentPage.value,
      pageSize: pageSize.value
    })

    results.value = response.items
    total.value = response.total

    if (keyword.value) {
      addToHistory(keyword.value)
    }
  } catch (err) {
    error.value = '搜索失败'
    console.error('搜索失败:', err)
  } finally {
    loading.value = false
  }
}

const handleSelectSuggestion = (suggestion: string) => {
  keyword.value = suggestion
  handleSearch()
}

const handleSelectHistory = (item: string) => {
  keyword.value = item
  handleSearch()
}

const handleClearHistory = () => {
  searchHistory.value = []
  saveSearchHistory()
  store.clearHistory()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  handleSearch()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  handleSearch()
}

const handleViewDetail = (id: string) => {
  emit('view-detail', id)
}

const addToHistory = (keyword: string) => {
  if (!searchHistory.value.includes(keyword)) {
    searchHistory.value.unshift(keyword)
    if (searchHistory.value.length > 10) {
      searchHistory.value.pop()
    }
    saveSearchHistory()
  }
}
</script>

<style scoped>
.search-page {
  padding: 20px;
}

.search-form {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
}

.error-message {
  color: #f56c6c;
  margin-bottom: 16px;
}

.search-suggestions {
  margin-bottom: 20px;
}

.suggestion-item {
  padding: 8px 16px;
  cursor: pointer;
}

.suggestion-item:hover {
  background-color: #f5f7fa;
}

.search-history {
  margin-bottom: 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-item {
  padding: 8px 16px;
  cursor: pointer;
}

.history-item:hover {
  background-color: #f5f7fa;
}

.search-results {
  margin-top: 20px;
}

.search-stats {
  margin-bottom: 16px;
  color: #606266;
}

.search-result-item {
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
}

.search-result-item:hover {
  background-color: #f5f7fa;
}

.item-meta {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
  display: flex;
  gap: 16px;
}

.relevance-score {
  color: #409eff;
}

.no-results {
  text-align: center;
  color: #909399;
  margin-top: 40px;
}
</style>