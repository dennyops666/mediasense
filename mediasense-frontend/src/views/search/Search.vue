<template>
  <div class="search-container">
    <!-- 搜索表单 -->
    <form @submit.prevent="handleSearch" class="search-form">
      <el-input
        v-model="searchKeyword"
        class="search-input"
        placeholder="请输入搜索关键词"
        @input="handleInput"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" native-type="submit">搜索</el-button>
    </form>

    <!-- 搜索建议 -->
    <div v-if="suggestions.length" class="suggestions">
      <div
        v-for="suggestion in suggestions"
        :key="suggestion"
        class="suggestion-item"
        @click="handleSuggestionClick(suggestion)"
      >
        {{ suggestion }}
      </div>
    </div>

    <!-- 过滤和排序 -->
    <div class="filters">
      <el-select v-model="selectedCategory" class="category-select" placeholder="选择分类">
        <el-option
          v-for="(count, category) in facets.categories"
          :key="category"
          :label="`${category} (${count})`"
          :value="category"
          class="category-option"
        />
      </el-select>

      <el-select v-model="selectedSource" class="source-select" placeholder="选择来源">
        <el-option
          v-for="(count, source) in facets.sources"
          :key="source"
          :label="`${source} (${count})`"
          :value="source"
          class="source-option"
        />
      </el-select>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="handleDateChange"
      />

      <el-select v-model="sortBy" class="sort-select" placeholder="排序方式">
        <el-option
          label="按日期"
          value="date"
          class="sort-option-date"
        />
        <el-option
          label="按相关度"
          value="relevance"
          class="sort-option-relevance"
        />
      </el-select>

      <el-select v-model="order" class="order-select" placeholder="排序顺序">
        <el-option
          label="升序"
          value="asc"
          class="order-option-asc"
        />
        <el-option
          label="降序"
          value="desc"
          class="order-option-desc"
        />
      </el-select>
    </div>

    <!-- 搜索结果 -->
    <div class="search-results">
      <div
        v-for="result in searchResults.items"
        :key="result.id"
        class="search-result-item"
        @click="handleResultClick(result)"
      >
        <h3>{{ result.title }}</h3>
        <p>{{ result.summary }}</p>
        <div class="meta">
          <span>{{ result.source }}</span>
          <span>{{ formatDate(result.publishTime) }}</span>
        </div>
      </div>
    </div>

    <!-- 热门搜索和历史记录 -->
    <div class="sidebar">
      <div class="hot-keywords">
        <h3>热门搜索</h3>
        <div
          v-for="keyword in hotKeywords"
          :key="keyword.keyword"
          class="hot-keyword"
          @click="handleKeywordClick(keyword.keyword)"
        >
          {{ keyword.keyword }} ({{ keyword.count }})
        </div>
      </div>

      <div class="search-history">
        <h3>搜索历史</h3>
        <div
          v-for="item in searchHistory"
          :key="item.timestamp"
          class="history-item"
          @click="handleKeywordClick(item.keyword)"
        >
          {{ item.keyword }}
          <span class="timestamp">{{ formatDate(item.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'
import { formatDate } from '@/utils/date'
import { debounce } from '@/utils/debounce'

const router = useRouter()
const searchStore = useSearchStore()

const searchKeyword = ref('')
const suggestions = ref<string[]>([])
const selectedCategory = ref('')
const selectedSource = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const sortBy = ref('relevance')
const order = ref('desc')

const searchResults = ref({
  total: 0,
  items: [],
  facets: {
    categories: {},
    sources: {}
  }
})

const hotKeywords = ref(searchStore.hotKeywords)
const searchHistory = ref(searchStore.searchHistory)
const facets = ref(searchStore.facets)

// 防抖处理输入
const handleInput = debounce(async (value: string) => {
  if (value.length > 0) {
    suggestions.value = await searchStore.fetchSuggestions(value)
  } else {
    suggestions.value = []
  }
}, 300)

// 处理搜索
const handleSearch = async () => {
  const params = {
    keyword: searchKeyword.value,
    category: selectedCategory.value,
    source: selectedSource.value,
    dateRange: dateRange.value,
    sortBy: sortBy.value,
    order: order.value
  }

  try {
    const results = await searchStore.search(params)
    searchResults.value = results
  } catch (error) {
    console.error('搜索失败:', error)
  }
}

// 处理建议点击
const handleSuggestionClick = (suggestion: string) => {
  searchKeyword.value = suggestion
  handleSearch()
}

// 处理结果点击
const handleResultClick = (result: any) => {
  router.push({
    name: 'news-detail',
    params: { id: result.id }
  })
}

// 处理关键词点击
const handleKeywordClick = (keyword: string) => {
  searchKeyword.value = keyword
  handleSearch()
}

// 处理日期变化
const handleDateChange = () => {
  searchStore.updateSearchParams({
    dateRange: dateRange.value
  })
}

// 监听过滤条件变化
watch([selectedCategory, selectedSource, sortBy, order], () => {
  searchStore.updateSearchParams({
    category: selectedCategory.value,
    source: selectedSource.value,
    sortBy: sortBy.value,
    order: order.value
  })
})
</script>

<style scoped>
.search-container {
  padding: 20px;
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
}

.search-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  grid-column: 1 / -1;
}

.search-input {
  flex: 1;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  z-index: 1000;
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
}

.suggestion-item:hover {
  background: #f5f7fa;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  grid-column: 1 / -1;
}

.search-results {
  grid-column: 1;
}

.search-result-item {
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-bottom: 15px;
  cursor: pointer;
}

.search-result-item:hover {
  background: #f5f7fa;
}

.meta {
  display: flex;
  gap: 15px;
  color: #909399;
  font-size: 0.9em;
}

.sidebar {
  grid-column: 2;
}

.hot-keywords,
.search-history {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.hot-keyword,
.history-item {
  padding: 5px 0;
  cursor: pointer;
}

.hot-keyword:hover,
.history-item:hover {
  color: #409eff;
}

.timestamp {
  color: #909399;
  font-size: 0.8em;
  margin-left: 10px;
}
</style> 