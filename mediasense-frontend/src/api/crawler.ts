import request from '@/utils/request'
import type { CrawlerConfig, CrawlerTask, CrawlerData, TaskQueryParams, DataQueryParams, PaginatedResponse } from '@/types/crawler'

/**
 * 获取爬虫配置列表
 */
export async function getCrawlerConfigs(): Promise<CrawlerConfig[]> {
  const { data } = await request.get('/crawler/configs')
  return data
}

/**
 * 获取单个爬虫配置
 */
export async function getCrawlerConfigById(id: string): Promise<CrawlerConfig> {
  const { data } = await request.get(`/crawler/configs/${id}`)
  return data
}

/**
 * 创建爬虫配置
 */
export async function createCrawlerConfig(config: Partial<CrawlerConfig>): Promise<CrawlerConfig> {
  const { data } = await request.post('/crawler/configs', config)
  return data
}

/**
 * 更新爬虫配置
 */
export async function updateCrawlerConfig(id: string, config: Partial<CrawlerConfig>): Promise<CrawlerConfig> {
  const { data } = await request.put(`/crawler/configs/${id}`, config)
  return data
}

/**
 * 删除爬虫配置
 */
export async function deleteCrawlerConfig(id: string): Promise<void> {
  await request.delete(`/crawler/configs/${id}`)
}

/**
 * 切换爬虫配置状态
 */
export async function toggleCrawlerConfig(id: string, enabled: boolean): Promise<CrawlerConfig> {
  const { data } = await request.put(`/crawler/configs/${id}/toggle`, { enabled })
  return data
}

/**
 * 运行爬虫任务
 */
export async function runCrawlerConfig(id: string): Promise<CrawlerTask> {
  const { data } = await request.post(`/crawler/configs/${id}/run`)
  return data
}

// 任务管理相关API
export const getTasks = async (params: TaskQueryParams) => {
  const { data } = await request.get<PaginatedResponse<CrawlerTask>>('/api/crawler/tasks', { params })
  return data
}

export const createTask = async (taskData: Omit<CrawlerTask, 'id'>) => {
  const { data } = await request.post<CrawlerTask>('/api/crawler/tasks', taskData)
  return data
}

export const updateTask = async (id: string, taskData: Partial<CrawlerTask>) => {
  const { data } = await request.put<CrawlerTask>(`/api/crawler/tasks/${id}`, taskData)
  return data
}

export const deleteTask = async (id: string) => {
  await request.delete(`/api/crawler/tasks/${id}`)
}

export const startTask = async (id: string) => {
  const { data } = await request.post(`/api/crawler/tasks/${id}/start`)
  return data
}

export const stopTask = async (id: string) => {
  const { data } = await request.post(`/api/crawler/tasks/${id}/stop`)
  return data
}

export const batchStartTasks = async (ids: string[]) => {
  const { data } = await request.post('/api/crawler/tasks/batch-start', { ids })
  return data
}

export const batchStopTasks = async (ids: string[]) => {
  const { data } = await request.post('/api/crawler/tasks/batch-stop', { ids })
  return data
}

// 配置管理相关API
export const getConfig = async (id: string) => {
  const { data } = await request.get<CrawlerConfig>(`/api/crawler/configs/${id}`)
  return data
}

export const saveConfig = async (id: string, configData: CrawlerConfig) => {
  const { data } = await request.put<CrawlerConfig>(`/api/crawler/configs/${id}`, configData)
  return data
}

// 数据管理相关API
export const getData = async (params: DataQueryParams) => {
  const { data } = await request.get<PaginatedResponse<CrawlerData>>('/api/crawler/data', { params })
  return data
}

export const deleteData = async (id: string) => {
  await request.delete(`/api/crawler/data/${id}`)
}

export const batchDeleteData = async (ids: string[]) => {
  await request.post('/api/crawler/data/batch-delete', { ids })
}

export const exportData = async (params: DataQueryParams) => {
  const response = await request.get('/api/crawler/data/export', { 
    params,
    responseType: 'blob'
  })
  return new Blob([response.data], { type: 'application/json' })
}

export default {
  getCrawlerConfigs,
  getCrawlerConfigById,
  createCrawlerConfig,
  updateCrawlerConfig,
  deleteCrawlerConfig,
  toggleCrawlerConfig,
  runCrawlerConfig,
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  startTask,
  stopTask,
  batchStartTasks,
  batchStopTasks,
  getConfig,
  saveConfig,
  getData,
  deleteData,
  batchDeleteData,
  exportData
} 