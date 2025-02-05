<template>
  <div class="news-detail-container" v-loading="newsStore.loading">
    <template v-if="newsStore.currentNews">
      <el-card class="news-card">
        <div class="news-header">
          <h1 class="news-title">{{ newsStore.currentNews.title }}</h1>
          <div class="news-meta">
            <div class="meta-item">
              <el-icon><user /></el-icon>
              <span>{{ newsStore.currentNews.author }}</span>
            </div>
            <div class="meta-item">
              <el-icon><link /></el-icon>
              <span>{{ newsStore.currentNews.source }}</span>
            </div>
            <div class="meta-item">
              <el-icon><timer /></el-icon>
              <span>{{ formatDate(newsStore.currentNews.publishTime) }}</span>
            </div>
            <el-tag size="small" type="info">
              {{ newsStore.currentNews.category }}
            </el-tag>
          </div>
        </div>

        <div class="news-summary">
          {{ newsStore.currentNews.summary }}
        </div>

        <div class="news-content" v-html="newsStore.currentNews.content" />

        <div class="news-tags">
          <el-icon><collection-tag /></el-icon>
          <el-tag
            v-for="tag in newsStore.currentNews.tags"
            :key="tag"
            size="small"
            class="tag-item"
          >
            {{ tag }}
          </el-tag>
        </div>

        <div class="news-actions">
          <el-button
            type="primary"
            :icon="Link"
            @click="openOriginalNews"
          >
            查看原文
          </el-button>
          <el-button :icon="Back" @click="router.back()">
            返回列表
          </el-button>
        </div>
      </el-card>
    </template>

    <el-empty
      v-else-if="!newsStore.loading"
      description="新闻不存在或已被删除"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/news')">
          返回新闻列表
        </el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  User,
  Link,
  Timer,
  Back,
  CollectionTag
} from '@element-plus/icons-vue'
import { useNewsStore } from '@/stores/news'
import { formatDate } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const newsStore = useNewsStore()

const openOriginalNews = () => {
  if (newsStore.currentNews?.url) {
    window.open(newsStore.currentNews.url, '_blank')
  }
}

onMounted(async () => {
  const newsId = route.params.id as string
  if (newsId) {
    await newsStore.fetchNewsDetail(newsId)
  }
})
</script>

<style scoped>
.news-detail-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.news-card {
  margin-bottom: 24px;
}

.news-header {
  margin-bottom: 24px;
}

.news-title {
  font-size: 28px;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
  line-height: 1.4;
}

.news-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.news-summary {
  font-size: 16px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  padding: 16px;
  background-color: var(--el-fill-color-lighter);
  border-radius: var(--el-border-radius-base);
  margin-bottom: 24px;
}

.news-content {
  font-size: 16px;
  line-height: 1.8;
  color: var(--el-text-color-primary);
  margin-bottom: 24px;
}

.news-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.tag-item {
  margin-right: 8px;
}

.news-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

:deep(.el-empty) {
  padding: 60px 0;
}
</style> 