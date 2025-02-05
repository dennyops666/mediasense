<template>
  <div class="home-page">
    <div class="hero-section">
      <h1 class="hero-title">MediaSense</h1>
      <p class="hero-subtitle">智能新闻聚合与舆情监控平台</p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="router.push('/news')">
          浏览新闻
        </el-button>
        <el-button size="large" @click="router.push('/search')">
          搜索新闻
        </el-button>
      </div>
    </div>

    <div class="features-section">
      <el-row :gutter="40">
        <el-col :span="8">
          <div class="feature-card">
            <el-icon class="feature-icon"><document /></el-icon>
            <h3>多源新闻聚合</h3>
            <p>汇集多家媒体平台的新闻资讯，提供全面的信息视角</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-card">
            <el-icon class="feature-icon"><search /></el-icon>
            <h3>智能搜索分析</h3>
            <p>强大的搜索功能，支持多维度筛选和智能分析</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="feature-card">
            <el-icon class="feature-icon"><trend-charts /></el-icon>
            <h3>舆情监控</h3>
            <p>实时监控热点话题，分析舆论走向</p>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="news-section" v-loading="newsStore.loading">
      <h2 class="section-title">最新资讯</h2>
      <el-row :gutter="20">
        <el-col
          v-for="news in newsStore.newsList.slice(0, 6)"
          :key="news.id"
          :span="8"
        >
          <el-card
            class="news-card"
            shadow="hover"
            @click="router.push(`/news/${news.id}`)"
          >
            <h3 class="news-title">{{ news.title }}</h3>
            <p class="news-summary">{{ news.summary }}</p>
            <div class="news-meta">
              <span>{{ news.source }}</span>
              <span>{{ getRelativeTime(news.publishTime) }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <div class="more-news">
        <el-button type="primary" text @click="router.push('/news')">
          查看更多
          <el-icon class="el-icon--right"><arrow-right /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/news'
import {
  Document,
  Search,
  TrendCharts,
  ArrowRight
} from '@element-plus/icons-vue'
import { getRelativeTime } from '@/utils/date'

const router = useRouter()
const newsStore = useNewsStore()

onMounted(async () => {
  await newsStore.fetchNews({
    page: 1,
    pageSize: 6
  })
})
</script>

<style scoped>
.home-page {
  padding: 40px 20px;
}

.hero-section {
  text-align: center;
  padding: 60px 0;
  background: linear-gradient(135deg, var(--el-color-primary-light-8) 0%, var(--el-color-primary-light-9) 100%);
  border-radius: var(--el-border-radius-base);
  margin-bottom: 60px;
}

.hero-title {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.hero-subtitle {
  font-size: 20px;
  color: var(--el-text-color-regular);
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.features-section {
  margin-bottom: 60px;
}

.feature-card {
  text-align: center;
  padding: 32px;
  background-color: var(--el-bg-color);
  border-radius: var(--el-border-radius-base);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 20px;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.feature-card p {
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.news-section {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: 28px;
  margin-bottom: 32px;
  text-align: center;
  color: var(--el-text-color-primary);
}

.news-card {
  height: 100%;
  cursor: pointer;
}

.news-title {
  font-size: 16px;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-summary {
  color: var(--el-text-color-regular);
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.more-news {
  text-align: center;
  margin-top: 32px;
}
</style> 