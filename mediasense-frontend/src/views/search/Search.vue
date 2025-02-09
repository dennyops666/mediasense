<template>
  <div class="search-container" data-test="search-container">
    <!-- 搜索表单 -->
    <div class="search-form" data-test="search-form">
      <el-input
        v-model="keyword"
        placeholder="请输入搜索关键词"
        @input="handleInput"
        @keyup.enter="handleSearch"
        @focus="showSuggestions = true"
        @blur="handleBlur"
        data-test="search-input"
      >
        <template #append>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleSearch"
            data-test="search-button"
          >
            搜索
          </el-button>
        </template>
      </el-input>

      <!-- 搜索建议 -->
      <div
        v-if="showSuggestions && suggestions.length > 0"
        class="suggestions"
        data-test="suggestion-list"
      >
        <div
          v-for="(suggestion, index) in suggestions"
          :key="index"
          class="suggestion-item"
          @click="handleSuggestionClick(suggestion)"
          @mousedown.prevent
          data-test="suggestion-item"
        >
          {{ suggestion }}
        </div>
      </div>

      <!-- 搜索历史 -->
      <div v-if="!keyword && searchHistory.length > 0" class="search-history" data-test="search-history">
        <div class="history-header" data-test="history-header">
          <span>搜索历史</span>
          <el-button
            text
            class="clear-history"
            @click="handleClearHistory"
            data-test="clear-history"
          >
            清空历史
          </el-button>
        </div>
        <div class="history-list" data-test="history-list">
          <div
            v-for="(item, index) in searchHistory"
            :key="index"
            class="history-item"
            @click="handleHistoryClick(item)"
            data-test="history-item"
          >
            {{ item }}
          </div>
        </div>
      </div>

      <!-- 高级搜索选项 -->
      <div class="advanced-search" data-test="advanced-search">
        <el-select
          v-model="searchParams.type"
          placeholder="选择类型"
          @change="handleTypeChange"
          data-test="type-select"
        >
          <el-option label="全部" value="" data-test="type-option-all" />
          <el-option label="新闻" value="news" data-test="type-option-news" />
          <el-option label="文章" value="article" data-test="type-option-article" />
        </el-select>

        <el-date-picker
          v-model="searchParams.date"
          type="date"
          placeholder="选择日期"
          @change="handleSearch"
          data-test="date-picker"
        />
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-loading="loading" class="search-results" data-test="search-results">
      <!-- 错误提示 -->
      <div v-if="error" class="error-message" data-test="error-alert">
        {{ error }}
      </div>

      <!-- 结果统计 -->
      <div v-if="searchResults.length > 0" class="search-stats" data-test="search-stats">
        找到 {{ searchStats.total }} 条结果 ({{ searchStats.time }}秒)
      </div>

      <!-- 结果列表 -->
      <div v-if="searchResults.length > 0" class="result-list" data-test="search-results-list">
        <div
          v-for="item in searchResults"
          :key="item.id"
          class="search-result-item"
          @click="handleResultClick(item.id)"
          data-test="search-result-item"
        >
          <h3 class="result-title" data-test="result-title">{{ item.title }}</h3>
          <p class="result-content" data-test="result-content">{{ item.content }}</p>
          <div class="result-meta" data-test="result-meta">
            <span class="result-source" data-test="result-source">{{ item.source }}</span>
            <span class="result-time" data-test="result-time">{{ item.publishTime }}</span>
            <span class="relevance-score" data-test="result-score">相关度: {{ item.score }}</span>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="searchResults.length > 0"
        :current-page="searchParams.page"
        :page-size="searchParams.pageSize"
        :total="total"
        @current-change="handlePageChange"
        class="pagination"
        data-test="pagination"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSearchStore } from '@/stores/search'
import { useRouter } from 'vue-router'
import { debounce } from 'lodash-es'

const store = useSearchStore()
const router = useRouter()

const keyword = ref('')
const showSuggestions = ref(false)
const showAdvanced = ref(false)

const searchParams = ref({
  keyword: '',
  type: '',
  date: null,
  page: 1,
  pageSize: 10
})

// 计算属性
const suggestions = computed(() => store.suggestions)
const searchResults = computed(() => store.searchResults)
const loading = computed(() => store.loading)
const error = computed(() => store.error)
const total = computed(() => store.total)
const searchHistory = computed(() => store.searchHistory)

// 搜索结果统计
const searchStats = computed(() => ({
  total: store.total,
  time: store.searchTime
}))

// 处理搜索
const handleSearch = async () => {
  if (!keyword.value.trim()) return
  
  searchParams.value.keyword = keyword.value
  await store.search(searchParams.value)
  showSuggestions.value = false
}

// 处理输入
const handleInput = debounce(async (value: string) => {
  if (value.trim()) {
    await store.getSuggestions(value)
    showSuggestions.value = true
  } else {
    showSuggestions.value = false
  }
}, 300)

// 处理建议点击
const handleSuggestionClick = (suggestion: string) => {
  keyword.value = suggestion
  handleSearch()
}

// 处理历史记录点击
const handleHistoryClick = (item: string) => {
  keyword.value = item
  handleSearch()
}

// 清空历史记录
const handleClearHistory = () => {
  store.clearHistory()
}

// 处理类型变化
const handleTypeChange = () => {
  handleSearch()
}

// 处理分页
const handlePageChange = (page: number) => {
  searchParams.value.page = page
  handleSearch()
}

// 处理结果点击
const handleResultClick = (id: number) => {
  router.push(`/detail/${id}`)
}

// 处理失焦
const handleBlur = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}
</script>

<style scoped>
.search-container {
  padding: 20px;
}

.search-form {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
}

.suggestions {
  position: absolute;
  width: 100%;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-top: 5px;
  z-index: 1000;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
}

.suggestion-item:hover {
  background-color: #f5f7fa;
}

.search-history {
  margin-top: 10px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.history-item {
  display: inline-block;
  margin-right: 10px;
  margin-bottom: 10px;
  padding: 4px 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
}

.history-item:hover {
  background-color: #e4e7ed;
}

.advanced-search {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.search-results {
  margin-top: 20px;
}

.error-message {
  color: #f56c6c;
  padding: 10px;
  border-radius: 4px;
  background-color: #fef0f0;
  margin-bottom: 10px;
}

.search-stats {
  color: #909399;
  margin-bottom: 10px;
}

.search-result-item {
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-result-item:hover {
  background-color: #f5f7fa;
}

.search-result-item h3 {
  margin: 0 0 8px;
  color: #303133;
}

.search-result-item p {
  margin: 0 0 8px;
  color: #606266;
}

.result-meta {
  color: #909399;
  font-size: 0.9em;
}

.result-meta span {
  margin-right: 15px;
}

.relevance-score {
  color: #409eff;
}
</style>