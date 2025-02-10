import { defineStore } from 'pinia'
import type { CrawlerTask, CrawlerConfig, CrawlerData, TaskQueryParams, DataQueryParams } from '@/types/crawler'
import * as crawlerApi from '@/api/crawler'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

export const useCrawlerStore = defineStore('crawler', () => {
  const tasks = ref<CrawlerTask[]>([])
  const currentTask = ref<CrawlerTask | null>(null)
  const currentConfig = ref<CrawlerConfig | null>(null)
  const configs = ref<CrawlerConfig[]>([])
  const data = ref<CrawlerData[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(10)

  const fetchTasks = async (params: TaskQueryParams) => {
    try {
      loading.value = true
      error.value = null
      const response = await crawlerApi.getTasks(params)
      tasks.value = response.data
      total.value = response.total
      currentPage.value = response.page
      pageSize.value = response.pageSize
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取任务列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createTask = async (task: Omit<CrawlerTask, 'id'>) => {
    try {
      const response = await crawlerApi.createTask(task)
      ElMessage.success('创建任务成功')
      return response
    } catch (err) {
      ElMessage.error('创建任务失败')
      throw err
    }
  }

  const updateTask = async (id: string, data: Partial<CrawlerTask>) => {
    try {
      const response = await crawlerApi.updateTask(id, data)
      ElMessage.success('更新任务成功')
      return response
    } catch (err) {
      ElMessage.error('更新任务失败')
      throw err
    }
  }

  const deleteTask = async (id: string) => {
    try {
      await crawlerApi.deleteTask(id)
      ElMessage.success('删除任务成功')
      await fetchTasks({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      ElMessage.error('删除任务失败')
      throw err
    }
  }

  const startTask = async (id: string) => {
    try {
      await crawlerApi.startTask(id)
      ElMessage.success('启动任务成功')
      await fetchTasks({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      throw new Error('启动任务失败')
    }
  }

  const stopTask = async (id: string) => {
    try {
      await crawlerApi.stopTask(id)
      ElMessage.success('停止任务成功')
      await fetchTasks({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      throw new Error('停止任务失败')
    }
  }

  const batchStartTasks = async (ids: string[]) => {
    try {
      await crawlerApi.batchStartTasks(ids)
      ElMessage.success('批量启动任务成功')
      await fetchTasks({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      throw new Error('批量启动任务失败')
    }
  }

  const batchStopTasks = async (ids: string[]) => {
    try {
      await crawlerApi.batchStopTasks(ids)
      ElMessage.success('批量停止任务成功')
      await fetchTasks({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      throw new Error('批量停止任务失败')
    }
  }

  const fetchConfig = async (id: string) => {
    try {
      const response = await crawlerApi.getConfig(id)
      currentConfig.value = response
      return response
    } catch (err) {
      ElMessage.error('获取配置失败')
      throw err
    }
  }

  const saveConfig = async (id: string, config: CrawlerConfig) => {
    try {
      const response = await crawlerApi.saveConfig(id, config)
      ElMessage.success('保存配置成功')
      return response
    } catch (err) {
      ElMessage.error('保存配置失败')
      throw err
    }
  }

  const fetchData = async (params: DataQueryParams) => {
    try {
      loading.value = true
      error.value = null
      const response = await crawlerApi.getData(params)
      if (!response || !response.items) {
        throw new Error('无效的数据格式')
      }
      data.value = response.items
      total.value = response.total || 0
      return {
        items: response.items,
        total: response.total || 0
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取数据失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteData = async (id: string) => {
    try {
      await crawlerApi.deleteData(id)
      ElMessage.success('删除数据成功')
      await fetchData({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      ElMessage.error('删除数据失败')
      throw err
    }
  }

  const batchDeleteData = async (ids: string[]) => {
    try {
      await crawlerApi.batchDeleteData(ids)
      ElMessage.success('批量删除数据成功')
      await fetchData({
        page: currentPage.value,
        pageSize: pageSize.value
      })
    } catch (err) {
      ElMessage.error('批量删除数据失败')
      throw err
    }
  }

  const exportData = async (params: DataQueryParams) => {
    try {
      const response = await crawlerApi.exportData(params)
      const url = window.URL.createObjectURL(new Blob([response]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `crawler-data-${new Date().getTime()}.xlsx`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      ElMessage.success('导出数据成功')
    } catch (err) {
      ElMessage.error('导出数据失败')
      throw err
    }
  }

  const fetchConfigs = async () => {
    try {
      loading.value = true
      const response = await crawlerApi.getCrawlerConfigs()
      configs.value = response
    } catch (err) {
      ElMessage.error('获取配置列表失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchConfigById = async (id: string) => {
    try {
      loading.value = true
      const response = await crawlerApi.getCrawlerConfigById(id)
      currentConfig.value = response
      return response
    } catch (err) {
      ElMessage.error('获取配置失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const createConfig = async (config: Partial<CrawlerConfig>) => {
    try {
      loading.value = true
      const response = await crawlerApi.createCrawlerConfig(config)
      await fetchConfigs()
      ElMessage.success('创建爬虫配置成功')
      return response
    } catch (err) {
      ElMessage.error('创建爬虫配置失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateConfig = async (id: string, config: Partial<CrawlerConfig>) => {
    try {
      loading.value = true
      const response = await crawlerApi.updateCrawlerConfig(id, config)
      await fetchConfigs()
      if (currentConfig.value?.id === id) {
        currentConfig.value = response
      }
      ElMessage.success('更新配置成功')
      return response
    } catch (err) {
      ElMessage.error('更新配置失败')
      throw err
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
      ElMessage.success('删除配置成功')
    } catch (err) {
      ElMessage.error('删除配置失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const toggleConfig = async (id: string, enabled: boolean) => {
    try {
      loading.value = true
      const response = await crawlerApi.toggleCrawlerConfig(id, enabled)
      await fetchConfigs()
      if (currentConfig.value?.id === id) {
        currentConfig.value = response
      }
      ElMessage.success(`${enabled ? '启用' : '禁用'}配置成功`)
      return response
    } catch (err) {
      ElMessage.error('切换状态失败')
      throw err
    } finally {
      loading.value = false
    }
  }

  const runConfig = async (id: string) => {
    try {
      loading.value = true
      const response = await crawlerApi.runCrawlerConfig(id)
      ElMessage.success('任务启动成功')
      return response
    } catch (err) {
      throw new Error('任务触发失败')
    } finally {
      loading.value = false
    }
  }

  return {
    tasks,
    currentTask,
    currentConfig,
    configs,
    data,
    total,
    loading,
    error,
    currentPage,
    pageSize,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    startTask,
    stopTask,
    batchStartTasks,
    batchStopTasks,
    fetchConfig,
    saveConfig,
    fetchData,
    deleteData,
    batchDeleteData,
    exportData,
    fetchConfigs,
    fetchConfigById,
    createConfig,
    updateConfig,
    deleteConfig,
    toggleConfig,
    runConfig
  }
}) 