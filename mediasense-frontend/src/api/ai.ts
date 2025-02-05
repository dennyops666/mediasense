import request from '@/utils/request'
import type {
  AIAnalysisRequest,
  AIAnalysisResponse,
  SentimentAnalysis,
  TextSummary,
  TopicAnalysis,
  TrendAnalysis
} from '@/types/api'

export const analyzeText = (data: AIAnalysisRequest) => {
  return request.post<AIAnalysisResponse>('/ai/analyze', data)
}

export const analyzeSentiment = (text: string) => {
  return request.post<SentimentAnalysis>('/ai/sentiment', { text })
}

export const generateSummary = (text: string, maxLength?: number) => {
  return request.post<TextSummary>('/ai/summary', { text, maxLength })
}

export const analyzeTopics = (text: string) => {
  return request.post<TopicAnalysis>('/ai/topics', { text })
}

export const analyzeTrends = (keyword: string, timeRange: [string, string]) => {
  return request.post<TrendAnalysis>('/ai/trends', { keyword, timeRange })
}

export const batchAnalyze = (texts: string[]) => {
  return request.post<SentimentAnalysis[]>('/ai/batch-analyze', { texts })
} 