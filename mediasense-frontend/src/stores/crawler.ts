import { defineStore } from 'pinia'
import type { CrawlerTask, CrawlerConfig, CrawlerData, TaskQueryParams, DataQueryParams } from '@/types/crawler'
import * as crawlerApi from '@/api/crawler'
import { ElMessage } from 'element-plus'

export const useCrawlerStore = defineStore('crawler', {
  state: () => ({
    tasks: [] as CrawlerTask[],
    currentTask: null as CrawlerTask | null,
    currentConfig: null as CrawlerConfig | null,
    configs: [] as CrawlerConfig[],
    data: [] as CrawlerData[],
    total: 0,
    loading: false,
    currentPage: 1,
    pageSize: 10
  }),

  actions: {
    async fetchTasks(params: TaskQueryParams) {
      try {
        this.loading = true
        const response = await crawlerApi.getTasks(params)
        this.tasks = response.data
        this.total = response.total
        this.currentPage = response.page
        this.pageSize = response.pageSize
      } catch (error) {
        ElMessage.error('获取任务列表失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    async createTask(task: Omit<CrawlerTask, 'id'>) {
      try {
        const response = await crawlerApi.createTask(task)
        ElMessage.success('创建任务成功')
        return response
      } catch (error) {
        ElMessage.error('创建任务失败')
        throw error
      }
    },

    async updateTask(id: string, data: Partial<CrawlerTask>) {
      try {
        const response = await crawlerApi.updateTask(id, data)
        ElMessage.success('更新任务成功')
        return response
      } catch (error) {
        ElMessage.error('更新任务失败')
        throw error
      }
    },

    async deleteTask(id: string) {
      try {
        await crawlerApi.deleteTask(id)
        ElMessage.success('删除任务成功')
        await this.fetchTasks({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('删除任务失败')
        throw error
      }
    },

    async startTask(id: string) {
      try {
        await crawlerApi.startTask(id)
        ElMessage.success('启动任务成功')
        await this.fetchTasks({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('启动任务失败')
        throw error
      }
    },

    async stopTask(id: string) {
      try {
        await crawlerApi.stopTask(id)
        ElMessage.success('停止任务成功')
        await this.fetchTasks({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('停止任务失败')
        throw error
      }
    },

    async batchStartTasks(ids: string[]) {
      try {
        await crawlerApi.batchStartTasks(ids)
        ElMessage.success('批量启动任务成功')
        await this.fetchTasks({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('批量启动任务失败')
        throw error
      }
    },

    async batchStopTasks(ids: string[]) {
      try {
        await crawlerApi.batchStopTasks(ids)
        ElMessage.success('批量停止任务成功')
        await this.fetchTasks({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('批量停止任务失败')
        throw error
      }
    },

    async fetchConfig(id: string) {
      try {
        const response = await crawlerApi.getConfig(id)
        this.currentConfig = response
        return response
      } catch (error) {
        ElMessage.error('获取配置失败')
        throw error
      }
    },

    async saveConfig(id: string, config: CrawlerConfig) {
      try {
        const response = await crawlerApi.saveConfig(id, config)
        ElMessage.success('保存配置成功')
        return response
      } catch (error) {
        ElMessage.error('保存配置失败')
        throw error
      }
    },

    async fetchData(params: DataQueryParams) {
      try {
        this.loading = true
        const response = await crawlerApi.getData(params)
        this.data = response.data
        this.total = response.total
        this.currentPage = response.page
        this.pageSize = response.pageSize
      } catch (error) {
        ElMessage.error('获取数据失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteData(id: string) {
      try {
        await crawlerApi.deleteData(id)
        ElMessage.success('删除数据成功')
        await this.fetchData({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('删除数据失败')
        throw error
      }
    },

    async batchDeleteData(ids: string[]) {
      try {
        await crawlerApi.batchDeleteData(ids)
        ElMessage.success('批量删除数据成功')
        await this.fetchData({
          page: this.currentPage,
          pageSize: this.pageSize
        })
      } catch (error) {
        ElMessage.error('批量删除数据失败')
        throw error
      }
    },

    async exportData(params: DataQueryParams) {
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
      } catch (error) {
        ElMessage.error('导出数据失败')
        throw error
      }
    },

    async fetchConfigs() {
      try {
        this.loading = true
        const response = await crawlerApi.getCrawlerConfigs()
        this.configs = response
      } catch (error) {
        ElMessage.error('获取配置列表失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchConfigById(id: string) {
      try {
        this.loading = true
        const response = await crawlerApi.getCrawlerConfigById(id)
        this.currentConfig = response
        return response
      } catch (error) {
        ElMessage.error('获取配置失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async createConfig(config: Partial<CrawlerConfig>) {
      try {
        this.loading = true
        const response = await crawlerApi.createCrawlerConfig(config)
        await this.fetchConfigs()
        ElMessage.success('创建爬虫配置成功')
        return response
      } catch (error) {
        ElMessage.error('创建爬虫配置失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateConfig(id: string, config: Partial<CrawlerConfig>) {
      try {
        this.loading = true
        const response = await crawlerApi.updateCrawlerConfig(id, config)
        await this.fetchConfigs()
        if (this.currentConfig?.id === id) {
          this.currentConfig = response
        }
        ElMessage.success('更新配置成功')
        return response
      } catch (error) {
        ElMessage.error('更新配置失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteConfig(id: string) {
      try {
        this.loading = true
        await crawlerApi.deleteCrawlerConfig(id)
        await this.fetchConfigs()
        if (this.currentConfig?.id === id) {
          this.currentConfig = null
        }
        ElMessage.success('删除配置成功')
      } catch (error) {
        ElMessage.error('删除配置失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async toggleConfig(id: string, enabled: boolean) {
      try {
        this.loading = true
        const response = await crawlerApi.toggleCrawlerConfig(id, enabled)
        await this.fetchConfigs()
        if (this.currentConfig?.id === id) {
          this.currentConfig = response
        }
        ElMessage.success(`${enabled ? '启用' : '禁用'}配置成功`)
        return response
      } catch (error) {
        ElMessage.error('切换状态失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    async runConfig(id: string) {
      try {
        this.loading = true
        const response = await crawlerApi.runCrawlerConfig(id)
        ElMessage.success('任务启动成功')
        return response
      } catch (error) {
        ElMessage.error('任务触发失败')
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 