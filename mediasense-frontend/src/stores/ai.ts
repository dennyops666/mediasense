import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  SentimentAnalysis,
  TextSummary,
  TopicAnalysis,
  TrendAnalysis
} from '@/types/api'
import * as aiApi from '@/api/ai'
import { ElMessage } from 'element-plus'

export const useAIStore = defineStore('ai', () => {
  const loading = ref(false)
  const sentimentResult = ref<SentimentAnalysis | null>(null)
  const summaryResult = ref<TextSummary | null>(null)
  const topicResult = ref<TopicAnalysis | null>(null)
  const trendResult = ref<TrendAnalysis | null>(null)

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

  const clearResults = () => {
    sentimentResult.value = null
    summaryResult.value = null
    topicResult.value = null
    trendResult.value = null
  }

  return {
    loading,
    sentimentResult,
    summaryResult,
    topicResult,
    trendResult,
    analyzeSentiment,
    generateSummary,
    analyzeTopics,
    analyzeTrends,
    clearResults
  }
}) 