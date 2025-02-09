import { vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// 创建基础的 store mock
export const createStoreMock = (name: string, state = {}, actions = {}, getters = {}) => {
  return {
    $id: name,
    $state: state,
    $patch: vi.fn(),
    $reset: vi.fn(),
    $subscribe: vi.fn(),
    $dispose: vi.fn(),
    ...state,
    ...actions,
    ...getters
  }
}

// 创建 auth store mock
export const createAuthStoreMock = () => createStoreMock('auth', {
  user: null,
  token: null,
  loading: false,
  error: null
}, {
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn()
})

// 创建 news store mock
export const createNewsStoreMock = () => createStoreMock('news', {
  newsList: [],
  newsDetail: null,
  loading: false,
  error: null,
  total: 0
}, {
  fetchNewsList: vi.fn(),
  fetchNewsDetail: vi.fn(),
  createNews: vi.fn(),
  updateNews: vi.fn(),
  deleteNews: vi.fn()
})

// 创建 search store mock
export const createSearchStoreMock = () => createStoreMock('search', {
  searchParams: {
    keyword: '',
    type: 'all',
    date: null,
    page: 1,
    pageSize: 10
  },
  results: [],
  loading: false,
  error: null,
  total: 0
}, {
  search: vi.fn(),
  setSearchParams: vi.fn(),
  updateSearchParams: vi.fn(),
  fetchSuggestions: vi.fn()
})

// 创建 monitor store mock
export const createMonitorStoreMock = () => createStoreMock('monitor', {
  systemMetrics: null,
  logs: [],
  metricsHistory: [],
  processList: [],
  diskUsage: null,
  serviceStatus: null,
  alerts: [],
  loading: false,
  error: null
}, {
  fetchMetrics: vi.fn(),
  fetchLogs: vi.fn(),
  fetchHistory: vi.fn(),
  fetchProcesses: vi.fn(),
  fetchDiskUsage: vi.fn(),
  fetchServiceStatus: vi.fn(),
  fetchAlerts: vi.fn(),
  confirmAlert: vi.fn(),
  restartService: vi.fn()
})

// 创建 ai store mock
export const createAIStoreMock = () => createStoreMock('ai', {
  config: {
    apiKey: 'test-api-key',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 2000
  },
  batchTasks: [],
  loading: false,
  error: null
}, {
  updateConfig: vi.fn(),
  testConnection: vi.fn(),
  createBatchTask: vi.fn(),
  updateBatchTask: vi.fn(),
  deleteBatchTask: vi.fn(),
  pauseBatchTask: vi.fn(),
  resumeBatchTask: vi.fn(),
  retryBatchTask: vi.fn()
})

// 创建 crawler store mock
export const createCrawlerStoreMock = () => createStoreMock('crawler', {
  configs: [],
  tasks: [],
  currentTask: null,
  loading: false,
  error: null
}, {
  fetchConfigs: vi.fn(),
  createConfig: vi.fn(),
  updateConfig: vi.fn(),
  deleteConfig: vi.fn(),
  testConfig: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
  exportData: vi.fn()
})

// 初始化 Pinia
export const initializePinia = () => {
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

export default {
  createStoreMock,
  createAuthStoreMock,
  createNewsStoreMock,
  createSearchStoreMock,
  createMonitorStoreMock,
  createAIStoreMock,
  createCrawlerStoreMock,
  initializePinia
} 