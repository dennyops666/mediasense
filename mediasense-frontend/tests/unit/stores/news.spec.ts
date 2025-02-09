import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useNewsStore } from '@/stores/news'
import axios from 'axios'

vi.mock('axios')

describe('News Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mockNewsList = [
    { id: 1, title: '测试新闻1', content: '内容1' },
    { id: 2, title: '测试新闻2', content: '内容2' }
  ]

  const mockNewsDetail = {
    id: 1,
    title: '测试新闻1',
    content: '详细内容1',
    source: '测试来源',
    publishTime: '2024-01-01'
  }

  const mockCategories = ['科技', '财经', '体育']
  const mockSources = ['新浪', '腾讯', '网易']

  it('应该有正确的初始状态', () => {
    const store = useNewsStore()
    expect(store.newsList).toEqual([])
    expect(store.newsDetail).toBeNull()
    expect(store.categories).toEqual([])
    expect(store.sources).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能获取新闻列表', async () => {
    const store = useNewsStore()
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockNewsList })

    await store.fetchNewsList()

    expect(axios.get).toHaveBeenCalledWith('/api/news')
    expect(store.newsList).toEqual(mockNewsList)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能获取新闻详情', async () => {
    const store = useNewsStore()
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockNewsDetail })

    await store.fetchNewsDetail(1)

    expect(axios.get).toHaveBeenCalledWith('/api/news/1')
    expect(store.newsDetail).toEqual(mockNewsDetail)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能获取新闻分类', async () => {
    const store = useNewsStore()
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockCategories })

    await store.fetchCategories()

    expect(axios.get).toHaveBeenCalledWith('/api/news/categories')
    expect(store.categories).toEqual(mockCategories)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能获取新闻来源', async () => {
    const store = useNewsStore()
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockSources })

    await store.fetchSources()

    expect(axios.get).toHaveBeenCalledWith('/api/news/sources')
    expect(store.sources).toEqual(mockSources)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能正确处理错误', async () => {
    const store = useNewsStore()
    const error = new Error('获取新闻失败')
    vi.mocked(axios.get).mockRejectedValueOnce(error)

    await store.fetchNewsList().catch(() => {})

    expect(store.loading).toBe(false)
    expect(store.error).toBe('获取新闻失败')
  })

  it('应该能按分类筛选新闻', async () => {
    const store = useNewsStore()
    const category = '科技'
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockNewsList.filter(n => n.category === category) })

    await store.fetchNewsByCategory(category)

    expect(axios.get).toHaveBeenCalledWith(`/api/news?category=${category}`)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('应该能按来源筛选新闻', async () => {
    const store = useNewsStore()
    const source = '新浪'
    vi.mocked(axios.get).mockResolvedValueOnce({ data: mockNewsList.filter(n => n.source === source) })

    await store.fetchNewsBySource(source)

    expect(axios.get).toHaveBeenCalledWith(`/api/news?source=${source}`)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })
}) 