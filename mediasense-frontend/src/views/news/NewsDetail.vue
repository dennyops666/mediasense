<template>
  <div class="news-detail">
    <el-skeleton v-if="loading" data-test="loading-skeleton">
      <template #template>
        <el-skeleton-item variant="h1" style="width: 50%" />
        <el-skeleton-item variant="text" style="width: 80%" />
        <el-skeleton-item variant="text" style="width: 70%" />
      </template>
    </el-skeleton>

    <el-alert
      v-else-if="error"
      type="error"
      :title="error"
      data-test="error-alert"
      show-icon
    />

    <div v-else-if="!currentNews" class="not-found">
      <el-empty description="新闻不存在" />
    </div>

    <el-card v-else class="news-card">
      <template #header>
        <div class="card-header">
          <h1 class="news-title">{{ currentNews.title }}</h1>
          <div class="news-meta">
            <span class="meta-item">
              <el-icon><User /></el-icon>
              {{ currentNews.author }}
            </span>
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              {{ currentNews.publishTime }}
            </span>
            <span class="meta-item">
              <el-icon><Link /></el-icon>
              <span data-test="news-source">{{ currentNews.source }}</span>
            </span>
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ currentNews.views }}
            </span>
          </div>
          <div class="news-tags">
            <el-tag
              v-for="tag in currentNews.tags"
              :key="tag"
              class="tag"
              data-test="news-tag"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </template>

      <div class="news-content">
        <el-image
          v-if="currentNews.imageUrl"
          :src="currentNews.imageUrl"
          data-test="news-image"
          fit="cover"
          class="news-image"
        />
        <div class="content-text">{{ currentNews.content }}</div>
      </div>

      <div class="news-actions">
        <el-button
          data-test="back-button"
          @click="handleBack"
        >
          <el-icon><Back /></el-icon>
          返回列表
        </el-button>
        <el-button
          type="primary"
          data-test="edit-button"
          @click="handleEdit"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button
          type="danger"
          data-test="delete-button"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
        <el-button
          type="success"
          data-test="share-button"
          @click="handleShare"
        >
          <el-icon><Share /></el-icon>
          分享
        </el-button>
      </div>
    </el-card>

    <el-dialog
      v-model="showEditDialog"
      title="编辑新闻"
      data-test="edit-dialog"
    >
      <el-form
        ref="editForm"
        :model="editForm"
        data-test="edit-form"
      >
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editForm.content" type="textarea" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="editForm.author" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editForm.source" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/news'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Link,
  Timer,
  Back,
  CollectionTag,
  Edit,
  Delete,
  View,
  Share
} from '@element-plus/icons-vue'

const props = defineProps<{
  id: string
}>()

const router = useRouter()
const store = useNewsStore()
const { currentNews, loading, error } = storeToRefs(store)

const showEditDialog = ref(false)
const editForm = ref({
  title: '',
  content: '',
  author: '',
  source: ''
})

const categories = ['政治', '经济', '科技', '文化', '体育']

onMounted(async () => {
  try {
    await store.fetchNewsDetail(props.id)
  } catch (err) {
    console.error('获取新闻详情失败:', err)
  }
})

const handleBack = () => {
  router.push({ name: 'NewsList' })
}

const handleEdit = () => {
  editForm.value = {
    title: currentNews.value.title,
    content: currentNews.value.content,
    author: currentNews.value.author,
    source: currentNews.value.source
  }
  showEditDialog.value = true
}

const handleEditSubmit = async () => {
  try {
    if (!currentNews.value) return
    
    const updatedNews = {
      ...currentNews.value,
      title: editForm.value.title,
      content: editForm.value.content,
      author: editForm.value.author,
      source: editForm.value.source
    }
    
    await store.updateNews(updatedNews)
    showEditDialog.value = false
    ElMessage.success('编辑成功')
  } catch (err) {
    console.error('编辑新闻失败:', err)
    ElMessage.error('编辑失败')
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这条新闻吗？', '提示', {
      type: 'warning'
    })
    await store.deleteNews(currentNews.value.id)
    ElMessage.success('删除成功')
    router.push({ name: 'NewsList' })
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除新闻失败:', err)
      ElMessage.error('删除失败')
    }
  }
}

const handleShare = () => {
  // 实现分享功能
  ElMessage.success('分享功能开发中')
}
</script>

<style scoped>
.news-detail {
  padding: 20px;
}

.news-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.news-meta {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.news-tags {
  display: flex;
  gap: 8px;
}

.news-content {
  margin-top: 20px;
}

.news-image {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  margin-bottom: 20px;
  border-radius: 4px;
}

.content-text {
  line-height: 1.6;
  color: #606266;
}

.news-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}
</style> 