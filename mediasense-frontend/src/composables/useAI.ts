import { ref } from 'vue'
import { useAIStore } from '@/stores/ai'

export function useAI() {
  const store = useAIStore()
  
  const sentiment = ref(null)
  const summary = ref(null)
  const topics = ref([])
  const trends = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const analyzeSentiment = async (text: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await store.analyzeSentiment(text)
      sentiment.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const generateSummary = async (text: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await store.generateSummary(text)
      summary.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const analyzeTopics = async (text: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await store.analyzeTopics(text)
      topics.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const analyzeTrends = async (text: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await store.analyzeTrends(text)
      trends.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    sentiment,
    summary,
    topics,
    trends,
    loading,
    error,

    // 方法
    analyzeSentiment,
    generateSummary,
    analyzeTopics,
    analyzeTrends
  }
}
