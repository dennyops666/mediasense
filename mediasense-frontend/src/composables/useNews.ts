import { ref, computed } from 'vue'
import { useNewsStore } from '@/stores/news'
import type { News, NewsCategory } from '@/types/news'
import dayjs from 'dayjs'

export function useNews() {
  const store = useNewsStore()
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 添加响应式数据
  const newsList = computed(() => store.newsList)
  const currentNews = computed(() => store.currentNews)
  const categories = computed(() => store.categories)
  const total = computed(() => store.total)

  const fetchNewsList = async (params: { page: number; pageSize: number; category?: string; keyword?: string }) => {
    try {
      loading.value = true
      error.value = null
      const result = await store.fetchNewsList(params)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取新闻列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchNewsDetail = async (id: string) => {
    try {
      loading.value = true
      error.value = null
      const result = await store.fetchNewsDetail(id)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取新闻详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createNews = async (news: Omit<News, 'id'>) => {
    try {
      loading.value = true
      error.value = null
      const result = await store.createNews(news)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建新闻失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateNews = async (id: string, news: Partial<News>) => {
    try {
      loading.value = true
      error.value = null
      const result = await store.updateNews(id, news)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新新闻失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteNews = async (id: string) => {
    try {
      loading.value = true
      error.value = null
      const result = await store.deleteNews(id)
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除新闻失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const formatPublishTime = (time: string) => {
    return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
  }

  const getNewsCategories = (): NewsCategory[] => {
    return [
      { id: 'tech', name: '科技' },
      { id: 'finance', name: '财经' },
      { id: 'sports', name: '体育' },
      { id: 'entertainment', name: '娱乐' }
    ]
  }

  return {
    // 状态
    loading,
    error,
    newsList,
    currentNews,
    categories,
    total,
    // 方法
    fetchNewsList,
    fetchNewsDetail,
    createNews,
    updateNews,
    deleteNews,
    formatPublishTime,
    getNewsCategories
  }
}

