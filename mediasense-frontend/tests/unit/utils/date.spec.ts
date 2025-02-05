import { describe, it, expect } from 'vitest'
import { formatDate, formatDateTime, formatDuration, getTimeAgo, getRelativeTime } from '@/utils/date'

describe('日期工具', () => {
  describe('formatDate', () => {
    it('应该正确格式化日期', () => {
      const date = new Date('2024-03-20T10:00:00Z')
      expect(formatDate(date)).toBe('2024-03-20')
      expect(formatDate(date, 'YYYY-MM-DD HH:mm:ss')).toBe('2024-03-20 18:00:00')
    })

    it('应该处理无效日期', () => {
      expect(formatDate(null)).toBe('-')
      expect(formatDate(undefined)).toBe('-')
      expect(formatDate('invalid')).toBe('-')
    })

    it('should format date correctly', () => {
      const date = new Date('2025-02-04T04:00:00Z')
      expect(formatDate(date)).toBe('2025-02-04')
      expect(formatDate(date, 'YYYY-MM-DD HH:mm:ss')).toBe('2025-02-04 12:00:00')
      expect(formatDate(date, 'HH:mm:ss')).toBe('12:00:00')
    })

    it('should handle invalid date', () => {
      expect(formatDate(null)).toBe('-')
      expect(formatDate(undefined)).toBe('-')
      expect(formatDate('invalid date')).toBe('-')
    })
  })

  describe('formatDateTime', () => {
    it('应该正确格式化日期时间', () => {
      const date = new Date('2024-03-20T10:00:00Z')
      expect(formatDateTime(date)).toBe('2024-03-20 18:00:00')
    })

    it('应该处理无效日期时间', () => {
      expect(formatDateTime(null)).toBe('-')
      expect(formatDateTime(undefined)).toBe('-')
      expect(formatDateTime('invalid')).toBe('-')
    })
  })

  describe('formatDuration', () => {
    it('应该正确格式化持续时间', () => {
      expect(formatDuration(60)).toBe('1分钟')
      expect(formatDuration(3600)).toBe('1小时')
      expect(formatDuration(3660)).toBe('1小时1分钟')
      expect(formatDuration(86400)).toBe('1天')
      expect(formatDuration(86460)).toBe('1天1分钟')
      expect(formatDuration(90000)).toBe('1天1小时')
    })

    it('应该处理无效持续时间', () => {
      expect(formatDuration(null)).toBe('-')
      expect(formatDuration(undefined)).toBe('-')
      expect(formatDuration(-1)).toBe('-')
    })
  })

  describe('getTimeAgo', () => {
    it('应该正确计算相对时间', () => {
      const now = new Date()
      const oneMinuteAgo = new Date(now.getTime() - 60 * 1000)
      const oneHourAgo = new Date(now.getTime() - 3600 * 1000)
      const oneDayAgo = new Date(now.getTime() - 24 * 3600 * 1000)
      const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 3600 * 1000)
      const oneYearAgo = new Date(now.getTime() - 365 * 24 * 3600 * 1000)

      expect(getTimeAgo(oneMinuteAgo)).toBe('1分钟前')
      expect(getTimeAgo(oneHourAgo)).toBe('1小时前')
      expect(getTimeAgo(oneDayAgo)).toBe('1天前')
      expect(getTimeAgo(oneMonthAgo)).toBe('1个月前')
      expect(getTimeAgo(oneYearAgo)).toBe('1年前')
    })

    it('应该处理未来时间', () => {
      const future = new Date(Date.now() + 1000)
      expect(getTimeAgo(future)).toBe('刚刚')
    })

    it('应该处理无效时间', () => {
      expect(getTimeAgo(null)).toBe('-')
      expect(getTimeAgo(undefined)).toBe('-')
      expect(getTimeAgo('invalid')).toBe('-')
    })
  })

  describe('getRelativeTime', () => {
    it('should return relative time correctly', () => {
      const now = new Date('2025-02-04T12:00:00')
      const oneMinuteAgo = new Date('2025-02-04T11:59:00')
      const oneHourAgo = new Date('2025-02-04T11:00:00')
      const oneDayAgo = new Date('2025-02-03T12:00:00')
      const oneWeekAgo = new Date('2025-01-28T12:00:00')
      const oneMonthAgo = new Date('2025-01-04T12:00:00')
      const oneYearAgo = new Date('2024-02-04T12:00:00')

      expect(getRelativeTime(now, now)).toBe('刚刚')
      expect(getRelativeTime(oneMinuteAgo, now)).toBe('1分钟前')
      expect(getRelativeTime(oneHourAgo, now)).toBe('1小时前')
      expect(getRelativeTime(oneDayAgo, now)).toBe('1天前')
      expect(getRelativeTime(oneWeekAgo, now)).toBe('1周前')
      expect(getRelativeTime(oneMonthAgo, now)).toBe('1个月前')
      expect(getRelativeTime(oneYearAgo, now)).toBe('1年前')
    })

    it('should handle invalid date', () => {
      const now = new Date()
      expect(getRelativeTime(null, now)).toBe('-')
      expect(getRelativeTime(undefined, now)).toBe('-')
      expect(getRelativeTime('invalid date', now)).toBe('-')
    })
  })
}) 