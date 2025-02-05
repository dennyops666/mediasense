<template>
  <div class="search-page">
    <div class="search-header">
      <h1 class="page-title">新闻搜索</h1>
      
      <div class="search-box">
        <el-input
          v-model="searchForm.keyword"
          placeholder="输入关键词搜索新闻"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><search /></el-icon>
          </template>
        </el-input>
        
        <el-button
          type="primary"
          :loading="searchStore.loading"
          @click="handleSearch"
        >
          搜索
        </el-button>
      </div>

      <div class="hot-searches" v-if="!searchStore.loading && !hasResults">
        <p class="section-title">热门搜索</p>
        <div class="hot-tags">
          <el-tag
            v-for="keyword in searchStore.hotSearches"
            :key="keyword"
            class="hot-tag"
            @click="handleHotSearch(keyword)"
          >
            {{ keyword }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="search-content" v-if="hasResults">
      <div class="filter-section">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <el-form-item label="分类">
            <el-select
              v-model="searchForm.category"
              placeholder="选择分类"
              clearable
            >
              <el-option
                v-for="[category, count] in Object.entries(searchStore.facets.categories)"
                :key="category"
                :label="`${category} (${count})`"
                :value="category"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="来源">
            <el-select
              v-model="searchForm.source"
              placeholder="选择来源"
              clearable
            >
              <el-option
                v-for="[source, count] in Object.entries(searchStore.facets.sources)"
                :key="source"
                :label="`${source} (${count})`"
                :value="source"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="排序">
            <el-select v-model="searchForm.sortBy">
              <el-option label="相关度" value="relevance" />
              <el-option label="时间" value="date" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="search-results">
        <div class="results-header">
          <p class="results-count">
            找到 {{ searchStore.total }} 条相关新闻
          </p>
        </div>

        <el-divider />

        <div class="results-list" v-loading="searchStore.loading">
          <template v-if="searchStore.searchResults.length">
            <div
              v-for="news in searchStore.searchResults"
              :key="news.id"
              class="result-item"
              @click="router.push(`/news/${news.id}`)"
            >
              <h3 class="result-title">{{ news.title }}</h3>
              <p class="result-summary">{{ news.summary }}</p>
              <div class="result-meta">
                <el-tag size="small" type="info">
                  {{ news.category }}
                </el-tag>
                <span class="meta-item">{{ news.source }}</span>
                <span class="meta-item">
                  {{ getRelativeTime(news.publishTime) }}
                </span>
              </div>
            </div>
          </template>
          
          <el-empty
            v-else
            description="未找到相关新闻"
          />
        </div>

        <div class="pagination" v-if="searchStore.total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="searchStore.total"
            :page-sizes="[10, 20, 30, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>

    <div class="search-tips" v-else-if="!searchStore.loading">
      <h3>搜索技巧</h3>
      <ul>
        <li>使用空格分隔多个关键词</li>
        <li>可以通过分类、来源等条件筛选</li>
        <li>支持按相关度或时间排序</li>
        <li>点击热门搜索标签快速开始</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'
import { getRelativeTime } from '@/utils/date'
import type { SearchParams } from '@/types/api'

const router = useRouter()
const searchStore = useSearchStore()

const currentPage = ref(1)
const pageSize = ref(10)

const searchForm = reactive<SearchParams>({
  keyword: '',
  category: undefined,
  source: undefined,
  dateRange: undefined,
  sortBy: 'relevance',
  order: 'desc',
  page: currentPage.value,
  pageSize: pageSize.value
})

const hasResults = computed(() => {
  return searchStore.searchResults.length > 0 || searchForm.keyword
})

const handleSearch = async () => {
  if (!searchForm.keyword) return
  currentPage.value = 1
  await searchStore.search({
    ...searchForm,
    page: currentPage.value,
    pageSize: pageSize.value
  })
}

const handleHotSearch = (keyword: string) => {
  searchForm.keyword = keyword
  handleSearch()
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    category: undefined,
    source: undefined,
    dateRange: undefined,
    sortBy: 'relevance',
    order: 'desc'
  })
  currentPage.value = 1
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  handleSearch()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  handleSearch()
}

onMounted(async () => {
  await searchStore.fetchHotSearches()
})
</script>

<style scoped>
.search-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-header {
  margin-bottom: 40px;
  text-align: center;
}

.page-title {
  font-size: 32px;
  color: var(--el-text-color-primary);
  margin-bottom: 24px;
}

.search-box {
  display: flex;
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.hot-searches {
  margin-top: 24px;
}

.section-title {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 16px;
}

.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.hot-tag {
  cursor: pointer;
}

.filter-section {
  margin-bottom: 24px;
  padding: 16px;
  background-color: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
}

.results-header {
  margin-bottom: 16px;
}

.results-count {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.result-item {
  padding: 20px 0;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.result-item:hover {
  background-color: var(--el-bg-color-page);
}

.result-title {
  font-size: 18px;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}

.result-summary {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
  line-height: 1.6;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.meta-item {
  color: var(--el-text-color-secondary);
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.search-tips {
  max-width: 600px;
  margin: 40px auto;
  padding: 24px;
  background-color: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
}

.search-tips h3 {
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.search-tips ul {
  color: var(--el-text-color-regular);
  line-height: 1.8;
  padding-left: 20px;
}
</style> 