import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  SentimentAnalysis,
  TextSummary,
  TopicAnalysis,
  TrendAnalysis,
  UsageStats,
  PerformanceStats,
  TaskStats,
  TrendData,
  ModelUsage,
  KeywordData
} from '@/types/api'
import * as aiApi from '@/api/ai'
import { ElMessage } from 'element-plus'

export const useAIStore = defineStore('ai', () => {
  const results = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const sentimentResult = ref<SentimentAnalysis | null>(null)
  const summaryResult = ref<TextSummary | null>(null)
  const topicResult = ref<TopicAnalysis | null>(null)
  const trendResult = ref<TrendAnalysis | null>(null)

  // 新增的状态
  const usageStats = ref<UsageStats>({
    totalCalls: 0,
    monthCalls: 0,
    remainingCredits: 0
  })
  const performanceStats = ref<PerformanceStats>({
    avgResponseTime: 0,
    successRate: 0
  })
  const taskStats = ref<TaskStats>({
    total: 0,
    success: 0,
    failed: 0
  })

  const keywordsResult = ref<KeywordData[]>([])

  const analyzeSentiment = async (text: string) => {
    try {
      loading.value = true
      const result = await aiApi.analyzeSentiment(text)
      sentimentResult.value = result
      return result
    } catch (error) {
      ElMessage.error('情感分析失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const generateSummary = async (text: string, maxLength?: number) => {
    try {
      loading.value = true
      const result = await aiApi.generateSummary(text, maxLength)
      summaryResult.value = result
      return result
    } catch (error) {
      ElMessage.error('生成摘要失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const analyzeTopics = async (text: string) => {
    try {
      loading.value = true
      const result = await aiApi.analyzeTopics(text)
      topicResult.value = result
      return result
    } catch (error) {
      ElMessage.error('主题分析失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const analyzeTrends = async (keyword: string, timeRange: [string, string]) => {
    try {
      loading.value = true
      const result = await aiApi.analyzeTrends(keyword, timeRange)
      trendResult.value = result
      return result
    } catch (error) {
      ElMessage.error('趋势分析失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 新增的方法
  const fetchUsage = async () => {
    try {
      const data = await aiApi.fetchUsageStats()
      usageStats.value = data
      return data
    } catch (error) {
      ElMessage.error('获取使用统计失败')
      throw error
    }
  }

  const fetchPerformance = async () => {
    try {
      const data = await aiApi.fetchPerformanceStats()
      performanceStats.value = data
      return data
    } catch (error) {
      ElMessage.error('获取性能统计失败')
      throw error
    }
  }

  const fetchTasks = async () => {
    try {
      const data = await aiApi.fetchTaskStats()
      taskStats.value = data
      return data
    } catch (error) {
      ElMessage.error('获取任务统计失败')
      throw error
    }
  }

  const fetchTrend = async (timeRange: string) => {
    try {
      const data = await aiApi.fetchTrendData(timeRange)
      return data
    } catch (error) {
      ElMessage.error('获取趋势数据失败')
      throw error
    }
  }

  const fetchModelUsage = async () => {
    try {
      const data = await aiApi.fetchModelUsageStats()
      return data
    } catch (error) {
      ElMessage.error('获取模型使用统计失败')
      throw error
    }
  }

  const fetchKeywords = async (timeRange: string): Promise<KeywordData[]> => {
    try {
      loading.value = true
      const data = await aiApi.fetchKeywords(timeRange)
      keywordsResult.value = data
      return data
    } catch (error) {
      ElMessage.error('获取关键词数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const clearResults = () => {
    sentimentResult.value = null
    summaryResult.value = null
    topicResult.value = null
    trendResult.value = null
    keywordsResult.value = []
    usageStats.value = {
      totalCalls: 0,
      monthCalls: 0,
      remainingCredits: 0
    }
    performanceStats.value = {
      avgResponseTime: 0,
      successRate: 0
    }
    taskStats.value = {
      total: 0,
      success: 0,
      failed: 0
    }
  }

  function $reset() {
    results.value = null
    loading.value = false
    error.value = null
    clearResults()
  }

  return {
    results,
    loading,
    error,
    sentimentResult,
    summaryResult,
    topicResult,
    trendResult,
    keywordsResult,
    usageStats,
    performanceStats,
    taskStats,
    analyzeSentiment,
    generateSummary,
    analyzeTopics,
    analyzeTrends,
    fetchKeywords,
    fetchUsage,
    fetchPerformance,
    fetchTasks,
    fetchTrend,
    fetchModelUsage,
    clearResults,
    $reset
  }
}) 