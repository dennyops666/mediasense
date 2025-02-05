<template>
  <div class="news-list">
    <div class="filter-section">
      <el-form :inline="true" :model="newsStore.filter">
        <el-form-item label="分类">
          <el-select
            v-model="newsStore.filter.category"
            placeholder="选择分类"
            clearable
            @change="handleFilterChange"
          >
            <el-option
              v-for="category in newsStore.categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="来源">
          <el-select
            v-model="newsStore.filter.source"
            placeholder="选择来源"
            clearable
            @change="handleFilterChange"
          >
            <el-option
              v-for="source in newsStore.sources"
              :key="source"
              :label="source"
              :value="source"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="newsStore.filter.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleFilterChange"
          />
        </el-form-item>

        <el-form-item label="关键词">
          <el-input
            v-model="newsStore.filter.keyword"
            placeholder="搜索关键词"
            clearable
            @keyup.enter="handleFilterChange"
          >
            <template #suffix>
              <el-icon class="search-icon" @click="handleFilterChange">
                <search />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </div>

    <div class="news-grid" v-loading="newsStore.loading">
      <el-empty v-if="!newsStore.newsList.length" description="暂无新闻" />
      
      <el-card
        v-for="news in newsStore.newsList"
        :key="news.id"
        class="news-card"
        @click="handleNewsClick(news.id)"
      >
        <template #header>
          <div class="news-header">
            <h3 class="news-title">{{ news.title }}</h3>
            <el-tag size="small" :type="getTagType(news.category)">
              {{ news.category }}
            </el-tag>
          </div>
        </template>

        <p class="news-summary">{{ news.summary }}</p>
        
        <div class="news-footer">
          <span class="news-source">
            <el-icon><location /></el-icon>
            {{ news.source }}
          </span>
          <span class="news-time">
            <el-icon><clock /></el-icon>
            {{ formatDate(news.publishTime) }}
          </span>
        </div>
      </el-card>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="newsStore.filter.page"
        v-model:page-size="newsStore.filter.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/news'
import { Search, Location, Clock } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import { storeToRefs } from 'pinia'

const router = useRouter()
const newsStore = useNewsStore()
const total = ref(0)

// 初始化数据
onMounted(async () => {
  await Promise.all([
    newsStore.fetchCategories(),
    newsStore.fetchSources(),
    newsStore.fetchNewsList()
  ])
})

// 处理筛选条件变化
const handleFilterChange = () => {
  newsStore.applyFilter(newsStore.filter)
}

// 处理分页变化
const handleSizeChange = (size: number) => {
  newsStore.applyFilter({ pageSize: size })
}

const handleCurrentChange = (page: number) => {
  newsStore.applyFilter({ page })
}

// 处理新闻点击
const handleNewsClick = (id: string) => {
  router.push(`/news/${id}`)
}

// 获取标签类型
const getTagType = (category: string) => {
  const types = {
    '政治': 'danger',
    '经济': 'success',
    '科技': 'primary',
    '文化': 'warning',
    '社会': 'info'
  }
  return types[category as keyof typeof types] || ''
}
</script>

<style scoped>
.news-list {
  padding: 20px;
}

.filter-section {
  margin-bottom: 24px;
  padding: 16px;
  background-color: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  box-shadow: var(--el-box-shadow-light);
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.news-card {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.news-card:hover {
  transform: translateY(-4px);
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.news-title {
  margin: 0;
  font-size: 16px;
  line-height: 1.4;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-summary {
  margin: 12px 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.news-source,
.news-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.search-icon {
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style> 