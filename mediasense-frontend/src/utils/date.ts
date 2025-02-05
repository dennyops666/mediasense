/**
 * 日期工具函数
 */

import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.locale('zh-cn')
dayjs.tz.setDefault('Asia/Shanghai')

/**
 * 格式化日期
 * @param date 日期
 * @param format 格式化模板
 */
export function formatDate(date: Date | string | null | undefined, format = 'YYYY-MM-DD'): string {
  if (!date) return '-'
  const d = dayjs(date)
  if (!d.isValid()) return '-'
  return d.tz('Asia/Shanghai').format(format)
}

/**
 * 格式化日期时间
 * @param date 日期
 */
export function formatDateTime(date: Date | string | null | undefined): string {
  if (!date) return '-'
  const d = dayjs(date)
  if (!d.isValid()) return '-'
  return d.tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化持续时间
 * @param seconds 秒数
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds < 0) return '-'

  const duration = dayjs.duration(seconds, 'seconds')
  const days = Math.floor(duration.asDays())
  const hours = duration.hours()
  const minutes = duration.minutes()
  const secs = duration.seconds()

  const parts = []

  if (days > 0) {
    parts.push(`${days}天`)
  }
  if (hours > 0) {
    parts.push(`${hours}小时`)
  }
  if (minutes > 0) {
    parts.push(`${minutes}分钟`)
  }
  if (secs > 0 && parts.length === 0) {
    parts.push(`${secs}秒`)
  }

  return parts.length > 0 ? parts.join('') : '0秒'
}

/**
 * 获取相对时间
 * @param date 日期
 * @param baseDate 基准日期
 */
export function getTimeAgo(date: Date | string | number | null | undefined, baseDate: Date = new Date()): string {
  if (!date) return '-'
  const d = dayjs(date)
  if (!d.isValid()) return '-'

  const now = dayjs(baseDate)
  if (d.isAfter(now)) return '刚刚'

  const diff = now.diff(d, 'second')
  if (diff < 30) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  if (diff < 2592000) return `${Math.floor(diff / 604800)}周前`
  if (diff < 31536000) return `${Math.floor(diff / 2592000)}个月前`
  return `${Math.floor(diff / 31536000)}年前`
}

/**
 * 获取相对时间（简化版）
 * @param date 日期
 * @param baseDate 基准日期
 */
export function getRelativeTime(date: Date | string | number | null | undefined, baseDate: Date = new Date()): string {
  if (!date) return '-'
  const d = dayjs(date)
  if (!d.isValid()) return '-'

  const now = dayjs(baseDate)
  if (d.isAfter(now)) return '刚刚'

  const diff = now.diff(d, 'second')
  if (diff < 30) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  if (diff < 2592000) return `1周前`
  if (diff < 31536000) return `${Math.floor(diff / 2592000)}个月前`
  return `${Math.floor(diff / 31536000)}年前`
}

export default {
  formatDate,
  formatDateTime,
  formatDuration,
  getTimeAgo,
  getRelativeTime
} 