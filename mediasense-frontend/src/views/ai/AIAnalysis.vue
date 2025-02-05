<template>
  <div class="ai-analysis">
    <el-tabs v-model="activeTab">
      <!-- 情感分析 -->
      <el-tab-pane label="情感分析" name="sentiment">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>文本情感分析</h3>
            </div>
          </template>
          
          <el-form>
            <el-form-item>
              <el-input
                v-model="sentimentText"
                type="textarea"
                :rows="4"
                placeholder="请输入要分析的文本"
                data-test="sentiment-input"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                @click="handleSentimentAnalysis"
                :loading="aiStore.loading"
                data-test="sentiment-analyze-btn"
              >
                开始分析
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="aiStore.sentimentResult" class="analysis-result">
            <el-descriptions border>
              <el-descriptions-item label="情感倾向">
                <el-tag :type="getSentimentType(aiStore.sentimentResult.sentiment)">
                  {{ getSentimentLabel(aiStore.sentimentResult.sentiment) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="情感得分">
                {{ (aiStore.sentimentResult.score * 100).toFixed(2) }}%
              </el-descriptions-item>
              <el-descriptions-item label="关键词">
                <el-tag
                  v-for="keyword in aiStore.sentimentResult.keywords"
                  :key="keyword"
                  class="mx-1"
                >
                  {{ keyword }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 文本摘要 -->
      <el-tab-pane label="文本摘要" name="summary">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>自动文本摘要</h3>
            </div>
          </template>
          
          <el-form>
            <el-form-item>
              <el-input
                v-model="summaryText"
                type="textarea"
                :rows="6"
                placeholder="请输入要生成摘要的文本"
                data-test="summary-input"
              />
            </el-form-item>
            <el-form-item>
              <el-input-number
                v-model="maxLength"
                :min="50"
                :max="500"
                :step="50"
                placeholder="最大摘要长度"
                data-test="max-length-input"
              />
              <el-button
                type="primary"
                @click="handleGenerateSummary"
                :loading="aiStore.loading"
                class="ml-2"
                data-test="generate-summary-btn"
              >
                生成摘要
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="aiStore.summaryResult" class="analysis-result">
            <h4>摘要结果：</h4>
            <p class="summary-text">{{ aiStore.summaryResult.summary }}</p>
            <h4>关键要点：</h4>
            <ul class="key-points">
              <li v-for="(point, index) in aiStore.summaryResult.keyPoints" :key="index">
                {{ point }}
              </li>
            </ul>
            <p class="word-count">
              原文字数：{{ aiStore.summaryResult.wordCount }}
              压缩比：{{ ((1 - aiStore.summaryResult.summary.length / aiStore.summaryResult.originalText.length) * 100).toFixed(1) }}%
            </p>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 主题分析 -->
      <el-tab-pane label="主题分析" name="topic">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>文本主题分析</h3>
            </div>
          </template>
          
          <el-form>
            <el-form-item>
              <el-input
                v-model="topicText"
                type="textarea"
                :rows="4"
                placeholder="请输入要分析的文本"
                data-test="topic-input"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                @click="handleTopicAnalysis"
                :loading="aiStore.loading"
                data-test="topic-analyze-btn"
              >
                分析主题
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="aiStore.topicResult" class="analysis-result">
            <el-collapse>
              <el-collapse-item
                v-for="topic in aiStore.topicResult.topics"
                :key="topic.name"
                :title="topic.name"
              >
                <p>置信度：{{ (topic.confidence * 100).toFixed(1) }}%</p>
                <div class="topic-keywords">
                  <el-tag
                    v-for="keyword in topic.keywords"
                    :key="keyword"
                    class="mx-1"
                  >
                    {{ keyword }}
                  </el-tag>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 趋势分析 -->
      <el-tab-pane label="趋势分析" name="trend">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>热点趋势分析</h3>
            </div>
          </template>
          
          <el-form>
            <el-form-item>
              <el-input
                v-model="trendKeyword"
                placeholder="请输入关键词"
                class="trend-keyword-input"
                data-test="trend-keyword-input"
              />
            </el-form-item>
            <el-form-item>
              <el-date-picker
                v-model="trendTimeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                :shortcuts="dateShortcuts"
              />
              <el-button
                type="primary"
                @click="handleTrendAnalysis"
                :loading="aiStore.loading"
                class="ml-2"
                data-test="trend-analyze-btn"
              >
                分析趋势
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="aiStore.trendResult" class="analysis-result">
            <div class="trend-chart">
              <v-chart class="chart" :option="trendChartOption" autoresize />
            </div>
            <h4>相关主题：</h4>
            <div class="related-topics">
              <el-tag
                v-for="topic in aiStore.trendResult.relatedTopics"
                :key="topic.topic"
                :type="getCorrelationType(topic.correlation)"
                class="mx-1"
              >
                {{ topic.topic }} ({{ (topic.correlation * 100).toFixed(1) }}%)
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAIStore } from '@/stores/ai'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { ECBasicOption } from 'echarts/types/dist/shared'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
])

const aiStore = useAIStore()
const activeTab = ref('sentiment')

// 情感分析
const sentimentText = ref('')
const handleSentimentAnalysis = async () => {
  if (!sentimentText.value.trim()) return
  await aiStore.analyzeSentiment(sentimentText.value)
}

const getSentimentType = (sentiment: string) => {
  const types: Record<string, string> = {
    positive: 'success',
    negative: 'danger',
    neutral: 'info'
  }
  return types[sentiment] || 'info'
}

const getSentimentLabel = (sentiment: string) => {
  const labels: Record<string, string> = {
    positive: '积极',
    negative: '消极',
    neutral: '中性'
  }
  return labels[sentiment] || '未知'
}

// 文本摘要
const summaryText = ref('')
const maxLength = ref(200)
const handleGenerateSummary = async () => {
  if (!summaryText.value.trim()) return
  await aiStore.generateSummary(summaryText.value, maxLength.value)
}

// 主题分析
const topicText = ref('')
const handleTopicAnalysis = async () => {
  if (!topicText.value.trim()) return
  await aiStore.analyzeTopics(topicText.value)
}

// 趋势分析
const trendKeyword = ref('')
const trendTimeRange = ref<[Date, Date] | null>(null)
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  },
  {
    text: '最近三月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    }
  }
]

const handleTrendAnalysis = async () => {
  if (!trendKeyword.value.trim() || !trendTimeRange.value) return
  const [start, end] = trendTimeRange.value
  await aiStore.analyzeTrends(
    trendKeyword.value,
    [start.toISOString(), end.toISOString()]
  )
}

const getCorrelationType = (correlation: number) => {
  if (correlation >= 0.7) return 'success'
  if (correlation >= 0.4) return 'warning'
  return 'info'
}

// 趋势图表配置
const trendChartOption = computed<ECBasicOption>(() => {
  if (!aiStore.trendResult) return {}
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: aiStore.trendResult.trends.map(t => t.date)
    },
    yAxis: [
      {
        type: 'value',
        name: '频率',
        position: 'left'
      },
      {
        type: 'value',
        name: '情感得分',
        position: 'right',
        min: -1,
        max: 1
      }
    ],
    series: [
      {
        name: '出现频率',
        type: 'line',
        data: aiStore.trendResult.trends.map(t => t.frequency),
        smooth: true
      },
      {
        name: '情感趋势',
        type: 'line',
        yAxisIndex: 1,
        data: aiStore.trendResult.trends.map(t => t.sentiment),
        smooth: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    ]
  }
})

// 切换标签页时清除结果
watch(activeTab, () => {
  aiStore.clearResults()
})
</script>

<style scoped>
.ai-analysis {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.analysis-result {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}

.summary-text {
  line-height: 1.6;
  color: var(--el-text-color-primary);
  background-color: var(--el-fill-color-light);
  padding: 16px;
  border-radius: 4px;
}

.key-points {
  padding-left: 20px;
  color: var(--el-text-color-regular);
}

.word-count {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-top: 16px;
}

.topic-keywords {
  margin-top: 8px;
}

.trend-keyword-input {
  width: 300px;
}

.trend-chart {
  height: 400px;
  margin: 20px 0;
}

.related-topics {
  margin-top: 12px;
}

.mx-1 {
  margin: 0 4px;
}

.ml-2 {
  margin-left: 8px;
}

:deep(.el-tag + .el-tag) {
  margin-left: 8px;
}
</style> 