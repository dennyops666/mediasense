import request from '@/utils/request'
import type {
  AIAnalysisRequest,
  AIAnalysisResponse,
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

export const analyzeText = (data: AIAnalysisRequest): Promise<AIAnalysisResponse> => {
  return request.post('/ai/analyze', data)
}

export const analyzeSentiment = (text: string): Promise<SentimentAnalysis> => {
  return request.post('/ai/sentiment', { text })
}

export const generateSummary = (text: string, maxLength?: number): Promise<TextSummary> => {
  return request.post('/ai/summary', { text, maxLength })
}

export const analyzeTopics = (text: string): Promise<TopicAnalysis> => {
  return request.post('/ai/topics', { text })
}

export const analyzeTrends = (keyword: string, timeRange: [string, string]): Promise<TrendAnalysis> => {
  return request.post('/ai/trends', { keyword, timeRange })
}

export const batchAnalyze = (texts: string[]): Promise<SentimentAnalysis[]> => {
  return request.post('/ai/batch-analyze', { texts })
}

export const fetchUsageStats = (): Promise<UsageStats> => {
  return request.get('/ai/stats/usage')
}

export const fetchPerformanceStats = (): Promise<PerformanceStats> => {
  return request.get('/ai/stats/performance')
}

export const fetchTaskStats = (): Promise<TaskStats> => {
  return request.get('/ai/stats/tasks')
}

export const fetchTrendData = (timeRange: string): Promise<TrendData> => {
  return request.get('/ai/stats/trend', {
    params: { timeRange }
  })
}

export const fetchModelUsageStats = (): Promise<ModelUsage[]> => {
  return request.get('/ai/stats/models')
}

export const fetchKeywords = (timeRange: string): Promise<KeywordData[]> => {
  return request.get('/ai/keywords', {
    params: { timeRange }
  })
}

export default {
  analyzeText,
  analyzeSentiment,
  generateSummary,
  analyzeTopics,
  analyzeTrends,
  batchAnalyze,
  fetchUsageStats,
  fetchPerformanceStats,
  fetchTaskStats,
  fetchTrendData,
  fetchModelUsageStats,
  fetchKeywords
} 