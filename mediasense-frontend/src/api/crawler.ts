import request from '@/utils/request'
import type { CrawlerConfig, CrawlerTask } from '@/types/crawler'

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

export default {
  getCrawlerConfigs,
  getCrawlerConfigById,
  createCrawlerConfig,
  updateCrawlerConfig,
  deleteCrawlerConfig,
  toggleCrawlerConfig,
  runCrawlerConfig
} 