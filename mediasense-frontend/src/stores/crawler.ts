import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CrawlerConfig } from '@/types/api'
import * as crawlerApi from '@/api/crawler'
import { ElMessage } from 'element-plus'

export const useCrawlerStore = defineStore('crawler', () => {
  const configs = ref<CrawlerConfig[]>([])
  const currentConfig = ref<CrawlerConfig | null>(null)
  const loading = ref(false)

  const fetchConfigs = async () => {
    try {
      loading.value = true
      const data = await crawlerApi.getCrawlerConfigs()
      configs.value = data
    } catch (error) {
      ElMessage.error('获取爬虫配置列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchConfigById = async (id: string) => {
    try {
      loading.value = true
      const data = await crawlerApi.getCrawlerConfigById(id)
      currentConfig.value = data
    } catch (error) {
      ElMessage.error('获取爬虫配置详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createConfig = async (data: Partial<CrawlerConfig>) => {
    try {
      loading.value = true
      await crawlerApi.createCrawlerConfig(data)
      await fetchConfigs()
      ElMessage.success('创建爬虫配置成功')
    } catch (error) {
      ElMessage.error('创建爬虫配置失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateConfig = async (id: string, data: Partial<CrawlerConfig>) => {
    try {
      loading.value = true
      await crawlerApi.updateCrawlerConfig(id, data)
      await fetchConfigs()
      if (currentConfig.value?.id === id) {
        await fetchConfigById(id)
      }
      ElMessage.success('更新爬虫配置成功')
    } catch (error) {
      ElMessage.error('更新爬虫配置失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteConfig = async (id: string) => {
    try {
      loading.value = true
      await crawlerApi.deleteCrawlerConfig(id)
      await fetchConfigs()
      if (currentConfig.value?.id === id) {
        currentConfig.value = null
      }
      ElMessage.success('删除爬虫配置成功')
    } catch (error) {
      ElMessage.error('删除爬虫配置失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const toggleConfig = async (id: string, enabled: boolean) => {
    try {
      loading.value = true
      await crawlerApi.toggleCrawlerConfig(id, enabled)
      await fetchConfigs()
      if (currentConfig.value?.id === id) {
        await fetchConfigById(id)
      }
      ElMessage.success(enabled ? '启用爬虫配置成功' : '禁用爬虫配置成功')
    } catch (error) {
      ElMessage.error(enabled ? '启用爬虫配置失败' : '禁用爬虫配置失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const runConfig = async (id: string) => {
    try {
      loading.value = true
      await crawlerApi.runCrawlerConfig(id)
      ElMessage.success('启动爬虫任务成功')
    } catch (error) {
      ElMessage.error('启动爬虫任务失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    configs,
    currentConfig,
    loading,
    fetchConfigs,
    fetchConfigById,
    createConfig,
    updateConfig,
    deleteConfig,
    toggleConfig,
    runConfig
  }
}) 